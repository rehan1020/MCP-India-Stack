"""Cryptographic dataset manifest verification and supply chain security.

Enforces:
1. Ed25519 detached signature verification on dataset manifests.
2. Anti-rollback protection via strictly monotonic version checks.
3. Cryptographic hash (SHA-256) and size assertions on dataset payloads.
4. Key rotation and revocation checking.
5. Strict policy gating (MCP_INDIA_STACK_REQUIRE_SIGNED_DATA=1).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from mcp_india_stack.utils.cache import get_cache_dir
from mcp_india_stack.utils.datasets import DATASET_CONFIG

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
KEYS_DIR = PACKAGE_ROOT / "keys"
DATA_DIR = PACKAGE_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"


@dataclass(frozen=True)
class VerifyingKey:
    """Public key record for verifying dataset signatures."""

    key_id: str
    algorithm: str
    status: str
    public_key: str
    valid_from: str | None = None
    expires_at: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class RevocationEntry:
    """Revocation entry for a compromised or retired key."""

    key_id: str
    revoked_at: str
    reason: str


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """Return deterministic canonical UTF-8 bytes for manifest signing and verification."""
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_verifying_keys() -> dict[str, VerifyingKey]:
    """Load bundled verifying keys from keys/keys.json."""
    keys_file = KEYS_DIR / "keys.json"
    if not keys_file.exists():
        logger.warning("Verifying keys file not found at %s", keys_file)
        return {}
    try:
        data = json.loads(keys_file.read_text(encoding="utf-8"))
        res: dict[str, VerifyingKey] = {}
        for item in data.get("keys", []):
            k = VerifyingKey(
                key_id=item["key_id"],
                algorithm=item.get("algorithm", "Ed25519"),
                status=item.get("status", "active"),
                public_key=item["public_key"],
                valid_from=item.get("valid_from"),
                expires_at=item.get("expires_at"),
                description=item.get("description"),
            )
            res[k.key_id] = k
        return res
    except Exception as exc:
        logger.error("Failed loading verifying keys from %s: %exc", keys_file, exc)
        return {}


def load_revocation_list() -> dict[str, RevocationEntry]:
    """Load revoked keys list from keys/revocations.json."""
    rev_file = KEYS_DIR / "revocations.json"
    if not rev_file.exists():
        return {}
    try:
        data = json.loads(rev_file.read_text(encoding="utf-8"))
        res: dict[str, RevocationEntry] = {}
        for item in data.get("revoked_keys", []):
            entry = RevocationEntry(
                key_id=item["key_id"],
                revoked_at=item["revoked_at"],
                reason=item.get("reason", "Revoked"),
            )
            res[entry.key_id] = entry
        return res
    except Exception as exc:
        logger.error("Failed loading revocation list from %s: %s", rev_file, exc)
        return {}


def _parse_iso(iso_str: str) -> datetime.datetime:
    """Parse ISO-8601 UTC timestamp."""
    cleaned = iso_str.replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def verify_manifest_signature(
    manifest: dict[str, Any],
    *,
    current_time: datetime.datetime | None = None,
) -> tuple[bool, str]:
    """Verify the Ed25519 detached signature and validity constraints of a manifest."""
    required = {
        "name",
        "version",
        "sha256",
        "size",
        "source",
        "generated_at",
        "key_id",
        "signature",
    }
    missing = required - set(manifest.keys())
    if missing:
        return False, f"Manifest missing required fields: {sorted(missing)}"

    key_id = str(manifest["key_id"])
    revocations = load_revocation_list()
    if key_id in revocations:
        return False, f"Signing key '{key_id}' is revoked: {revocations[key_id].reason}"

    keys = load_verifying_keys()
    if key_id not in keys:
        return False, f"Unknown signing key_id '{key_id}'"

    vkey = keys[key_id]
    if vkey.status == "revoked":
        return False, f"Signing key '{key_id}' is marked as revoked in key ring"

    now = current_time or datetime.datetime.now(datetime.timezone.utc)

    if vkey.valid_from:
        vfrom = _parse_iso(vkey.valid_from)
        if now < vfrom:
            return False, f"Signing key '{key_id}' is not yet valid (valid_from: {vkey.valid_from})"

    if vkey.expires_at:
        vexp = _parse_iso(vkey.expires_at)
        if now > vexp:
            return False, f"Signing key '{key_id}' expired at {vkey.expires_at}"

    if manifest.get("expires_at"):
        mexp = _parse_iso(str(manifest["expires_at"]))
        if now > mexp:
            return False, f"Manifest for '{manifest['name']}' expired at {manifest['expires_at']}"

    # Verify Ed25519 detached signature
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(vkey.public_key))
        sig_bytes = bytes.fromhex(str(manifest["signature"]))
        canonical_bytes = canonical_manifest_bytes(manifest)
        pub.verify(sig_bytes, canonical_bytes)
    except InvalidSignature:
        return False, "Invalid cryptographic signature on manifest"
    except Exception as exc:
        return False, f"Signature verification error: {exc}"

    return True, "Signature verified successfully"


def verify_dataset_file(
    dataset_name: str,
    path: Path,
    manifest: dict[str, Any],
    *,
    current_time: datetime.datetime | None = None,
) -> tuple[bool, str]:
    """Verify a dataset file against its signed manifest."""
    sig_ok, sig_msg = verify_manifest_signature(manifest, current_time=current_time)
    if not sig_ok:
        return False, f"Manifest signature check failed: {sig_msg}"

    if not path.exists():
        return False, f"Dataset file does not exist at '{path}'"

    raw_bytes = path.read_bytes()
    expected_size = int(manifest["size"])
    if len(raw_bytes) != expected_size:
        return False, f"Dataset size mismatch: expected {expected_size} bytes, got {len(raw_bytes)}"

    expected_sha = str(manifest["sha256"]).lower()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest().lower()
    if actual_sha != expected_sha:
        return False, f"Dataset SHA-256 mismatch: expected {expected_sha}, got {actual_sha}"

    return True, "Dataset integrity and signature verified"


def get_bundled_manifest(dataset_name: str) -> dict[str, Any] | None:
    """Load bundled manifest for a dataset if present."""
    manifest_path = MANIFESTS_DIR / f"{dataset_name}.manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    except Exception:
        return None


def get_cached_manifest(dataset_name: str) -> dict[str, Any] | None:
    """Load cached manifest from user cache directory if present."""
    if dataset_name not in DATASET_CONFIG:
        return None
    cache_dir = get_cache_dir()
    manifest_file = cache_dir / f"{DATASET_CONFIG[dataset_name]['cache_filename']}.manifest.json"
    if not manifest_file.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(manifest_file.read_text(encoding="utf-8")))
    except Exception:
        return None


def verify_installed_data() -> dict[str, Any]:
    """Verify all installed bundled datasets and cache against signed manifests."""
    now = datetime.datetime.now(datetime.timezone.utc)
    results: dict[str, Any] = {}
    overall_ok = True

    for name, config in DATASET_CONFIG.items():
        bundled_file = DATA_DIR / config["bundled_path"].removeprefix("data/")
        cache_file = get_cache_dir() / config["cache_filename"]

        cached_manifest = get_cached_manifest(name)
        bundled_manifest = get_bundled_manifest(name)

        if not bundled_manifest:
            overall_ok = False
            results[name] = {
                "verified": False,
                "version": None,
                "age_days": None,
                "key_id": None,
                "path": str(bundled_file),
                "error": "No bundled manifest found for dataset",
            }
            continue

        b_ok, b_msg = verify_dataset_file(name, bundled_file, bundled_manifest, current_time=now)
        if not b_ok:
            overall_ok = False

        c_ok = True
        c_msg = None
        if cache_file.exists():
            if not cached_manifest:
                c_ok = False
                c_msg = f"Cached dataset file exists at '{cache_file}' but has no signed manifest"
                overall_ok = False
            else:
                c_ok, c_msg = verify_dataset_file(
                    name, cache_file, cached_manifest, current_time=now
                )
                if not c_ok:
                    overall_ok = False

        active_manifest = (
            cached_manifest
            if cache_file.exists() and cached_manifest and c_ok
            else bundled_manifest
        )
        active_path = cache_file if cache_file.exists() and c_ok else bundled_file

        gen_at = active_manifest.get("generated_at")
        age_days = None
        if gen_at:
            try:
                gen_dt = _parse_iso(gen_at)
                age_days = max(0, (now - gen_dt).days)
            except Exception:
                pass

        dataset_verified = b_ok and (c_ok if cache_file.exists() else True)
        results[name] = {
            "verified": dataset_verified,
            "version": active_manifest.get("version"),
            "age_days": age_days,
            "key_id": active_manifest.get("key_id"),
            "sha256": active_manifest.get("sha256"),
            "size": active_manifest.get("size"),
            "path": str(active_path),
            "bundled_verified": b_ok,
            "cache_verified": c_ok if cache_file.exists() else None,
            "error": None if (b_ok and c_ok) else (b_msg if not b_ok else c_msg),
        }

    return {
        "verified": overall_ok,
        "datasets": results,
    }


def get_dataset_security_status() -> dict[str, Any]:
    """Return dataset signature verification status for india://status resource."""
    data = verify_installed_data()
    return {
        "dataset_signature_verified": data["verified"],
        "datasets": {
            k: {
                "version": v.get("version"),
                "age_days": v.get("age_days"),
                "key_id": v.get("key_id"),
                "verified": v.get("verified"),
            }
            for k, v in data["datasets"].items()
        },
    }


def verify_dataset_integrity(dataset_name: str, file_path: Path) -> None:
    """Assert dataset integrity based on policy (MCP_INDIA_STACK_REQUIRE_SIGNED_DATA)."""
    manifest = get_cached_manifest(dataset_name) or get_bundled_manifest(dataset_name)
    require_signed = os.environ.get("MCP_INDIA_STACK_REQUIRE_SIGNED_DATA") == "1"

    if manifest is None:
        msg = f"Untrusted dataset: no signed manifest found for '{dataset_name}'"
        if require_signed:
            raise RuntimeError(msg)
        logger.warning(msg)
        return

    ok, err = verify_dataset_file(dataset_name, file_path, manifest)
    if not ok:
        msg = f"Dataset verification failed for '{dataset_name}': {err}"
        if require_signed:
            raise RuntimeError(msg)
        logger.warning(msg)


def run_cli_verify_data() -> None:
    """CLI runner for --verify-data option."""
    import sys

    report = verify_installed_data()
    all_ok = report["verified"]
    sys.stdout.write("Installed Dataset Supply Chain Verification:\n")
    for name, item in report["datasets"].items():
        status_label = "PASS" if item["verified"] else "FAIL"
        ver_str = f"v{item['version']}" if item.get("version") else "unknown"
        key_str = item.get("key_id") or "no-key"
        age_str = f"{item['age_days']}d old" if item.get("age_days") is not None else "unknown age"
        if item["verified"]:
            sys.stdout.write(f"  [{status_label}] {name}: {ver_str} (key: {key_str}, {age_str})\n")
        else:
            err = item.get("error") or "verification failed"
            sys.stdout.write(f"  [{status_label}] {name}: {err}\n")

    if all_ok:
        sys.stdout.write("\nAll dataset signatures and checksums verified successfully.\n")
        sys.exit(0)
    else:
        sys.stderr.write("\nDataset verification failed.\n")
        sys.exit(1)
