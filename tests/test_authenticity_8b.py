"""Tests for Authenticity 8b: Signed dataset manifests and supply chain verification.

Verifies:
1. Tampered dataset detection (hash/size mismatch).
2. Invalid Ed25519 signature rejection.
3. Expired manifest rejection.
4. Revoked key rejection.
5. Unknown key_id rejection.
6. Monotonic anti-rollback protection on CDN refresh.
7. Atomic failure recovery keeping last-good data.
8. Offline verification CLI output and return codes (`--verify-data`).
9. Strict policy gating (`MCP_INDIA_STACK_REQUIRE_SIGNED_DATA=1`).
10. `india://status` supply-chain metadata reporting.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from mcp_india_stack.authenticity.manifest import (
    canonical_manifest_bytes,
    verify_dataset_file,
    verify_dataset_integrity,
    verify_manifest_signature,
)
from mcp_india_stack.network.cdn_refresh import CdnRefreshError, refresh_dataset
from mcp_india_stack.server import server_status
from mcp_india_stack.utils.datasets import DATASET_CONFIG

# Test key materials
PRIMARY_PRIV_HEX = "ac803eb1a635fb8d033a31b5d2b2ffdf5d0d43ca3622a8f071c83859bf405a17"
REVOKED_PRIV_HEX = "1565b78361acc89da4277f4b16cce218f878890ea37bdd251134104887246368"


def _create_signed_manifest(
    name: str,
    payload: bytes,
    *,
    version: int = 20260101,
    key_id: str = "mcp-india-stack-ed25519-primary",
    priv_hex: str = PRIMARY_PRIV_HEX,
    expires_at: str | None = "2030-12-31T23:59:59Z",
    generated_at: str = "2026-11-04T00:00:00Z",
) -> dict[str, Any]:
    """Helper to create and sign a dataset manifest."""
    manifest = {
        "name": name,
        "version": version,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
        "source": "Test Authority",
        "generated_at": generated_at,
        "expires_at": expires_at,
        "key_id": key_id,
    }
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))
    sig = priv.sign(canonical_manifest_bytes(manifest))
    manifest["signature"] = sig.hex()
    return manifest


def test_tampered_dataset_detection(tmp_path: Path) -> None:
    """Tampering with dataset bytes causes SHA-256 and size verification to fail."""
    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest("ifsc", sample_data)

    data_file = tmp_path / "IFSC.csv"
    data_file.write_bytes(sample_data)

    # Valid check passes
    ok, msg = verify_dataset_file("ifsc", data_file, manifest)
    assert ok is True

    # Mutate 1 byte
    tampered_data = bytearray(sample_data)
    tampered_data[0] = ord(b"X")
    data_file.write_bytes(tampered_data)

    ok_bad, msg_bad = verify_dataset_file("ifsc", data_file, manifest)
    assert ok_bad is False
    assert "SHA-256 mismatch" in msg_bad


def test_invalid_signature_rejection() -> None:
    """Tampered manifest or invalid signature must be rejected."""
    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest("ifsc", sample_data)

    # Corrupt the signature hex
    bad_manifest = dict(manifest)
    bad_manifest["signature"] = "00" * 64

    ok, msg = verify_manifest_signature(bad_manifest)
    assert ok is False
    assert "Invalid cryptographic signature" in msg or "verification error" in msg

    # Modify a field without re-signing
    tampered_manifest = dict(manifest)
    tampered_manifest["version"] = 99999999
    ok2, msg2 = verify_manifest_signature(tampered_manifest)
    assert ok2 is False
    assert "Invalid cryptographic signature" in msg2


def test_expired_manifest_rejection() -> None:
    """Manifest past expires_at timestamp is rejected."""
    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest(
        "ifsc",
        sample_data,
        expires_at="2020-01-01T00:00:00Z",
    )

    ok, msg = verify_manifest_signature(manifest)
    assert ok is False
    assert "expired" in msg.lower()


def test_revoked_key_rejection() -> None:
    """Manifest signed with a revoked key is rejected."""
    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest(
        "ifsc",
        sample_data,
        key_id="mcp-india-stack-ed25519-revoked-sample",
        priv_hex=REVOKED_PRIV_HEX,
    )

    ok, msg = verify_manifest_signature(manifest)
    assert ok is False
    assert "revoked" in msg.lower()


def test_unknown_key_id_rejection() -> None:
    """Manifest signed with unknown key_id is rejected."""
    priv = Ed25519PrivateKey.generate()
    priv_hex = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()

    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest(
        "ifsc",
        sample_data,
        key_id="mcp-india-stack-ed25519-rogue-key-999",
        priv_hex=priv_hex,
    )

    ok, msg = verify_manifest_signature(manifest)
    assert ok is False
    assert "unknown signing key_id" in msg.lower()


def test_cdn_refresh_monotonic_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject incoming manifest when incoming version <= current version."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))

    sample_data = (
        b"BANK,IFSC,BRANCH,ADDRESS,CONTACT,CITY,DISTRICT,STATE,CENTRE,MICR,UPI,RTGS,NEFT,IMPS,SWIFT\n"
        b"GoodBank,GOOD0001,Main,Addr,123,City,Dist,State,Centre,123,true,true,true,true,SWIFT\n"
    )
    manifest = _create_signed_manifest("ifsc", sample_data, version=20250401)

    # Current version is 20250401; incoming is 20250401 (<= current)
    with pytest.raises(CdnRefreshError, match="(?i)rollback|older version"):
        refresh_dataset(
            "ifsc",
            mock_payload=sample_data,
            mock_manifest=manifest,
            current_version=20250401,
        )


def test_cdn_refresh_atomic_failure_keeps_last_good(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed refresh with invalid signature does not touch existing cache file."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))

    cache_file = tmp_path / "IFSC.csv"
    original_data = (
        "BANK,IFSC,BRANCH,ADDRESS,CONTACT,CITY,DISTRICT,STATE,CENTRE,MICR,UPI,RTGS,NEFT,IMPS,SWIFT\n"
        "OriginalBank,ORIG0001,Main,Addr,123,City,Dist,State,Centre,123,true,true,true,true,SWIFT\n"
    )
    cache_file.write_text(original_data, encoding="utf-8")

    sample_data = (
        b"BANK,IFSC,BRANCH,ADDRESS,CONTACT,CITY,DISTRICT,STATE,CENTRE,MICR,UPI,RTGS,NEFT,IMPS,SWIFT\n"
        b"NewBank,NEW0001,Main,Addr,123,City,Dist,State,Centre,123,true,true,true,true,SWIFT\n"
    )
    manifest = _create_signed_manifest("ifsc", sample_data, version=20260101)
    # Corrupt signature
    manifest["signature"] = "11" * 64

    with pytest.raises(CdnRefreshError, match="(?i)signature"):
        refresh_dataset(
            "ifsc",
            mock_payload=sample_data,
            mock_manifest=manifest,
        )

    assert cache_file.exists()
    assert cache_file.read_text(encoding="utf-8") == original_data


def test_cdn_refresh_successful_with_signed_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Valid signed manifest refreshes cache atomically and writes manifest."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))

    sample_data = (
        b"BANK,IFSC,BRANCH,ADDRESS,CONTACT,CITY,DISTRICT,STATE,CENTRE,MICR,UPI,RTGS,NEFT,IMPS,SWIFT\n"
        b"NextBank,NEXT0001,Main,Addr,123,City,Dist,State,Centre,123,true,true,true,true,SWIFT\n"
    )
    manifest = _create_signed_manifest("ifsc", sample_data, version=20270101)

    ok = refresh_dataset(
        "ifsc",
        mock_payload=sample_data,
        mock_manifest=manifest,
        current_version=20250401,
    )
    assert ok is True

    cache_file = tmp_path / "IFSC.csv"
    manifest_file = tmp_path / "IFSC.csv.manifest.json"
    assert cache_file.exists()
    assert manifest_file.exists()
    assert cache_file.read_bytes() == sample_data

    # Verify cached manifest integrity
    cached_m = json.loads(manifest_file.read_text(encoding="utf-8"))
    v_ok, _ = verify_dataset_file("ifsc", cache_file, cached_m)
    assert v_ok is True


def test_policy_require_signed_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MCP_INDIA_STACK_REQUIRE_SIGNED_DATA=1 raises on corrupt dataset; default warns."""
    sample_data = b"BANK,IFSC,BRANCH\nGoodBank,GOOD0001,Main\n"
    manifest = _create_signed_manifest("ifsc", sample_data)
    data_file = tmp_path / "IFSC.csv"
    data_file.write_bytes(b"corrupt")

    # Mock bundled manifest lookup for this test
    monkeypatch.setattr(
        "mcp_india_stack.authenticity.manifest.get_bundled_manifest",
        lambda _: manifest,
    )
    monkeypatch.setattr(
        "mcp_india_stack.authenticity.manifest.get_cached_manifest",
        lambda _: None,
    )

    # 1. Default (no strict env flag) logs warning and does not raise
    monkeypatch.delenv("MCP_INDIA_STACK_REQUIRE_SIGNED_DATA", raising=False)
    verify_dataset_integrity("ifsc", data_file)

    # 2. Strict policy raises RuntimeError
    monkeypatch.setenv("MCP_INDIA_STACK_REQUIRE_SIGNED_DATA", "1")
    with pytest.raises(RuntimeError, match="(?i)Dataset verification failed"):
        verify_dataset_integrity("ifsc", data_file)


def test_server_status_signed_data_fields() -> None:
    """india://status additively reports dataset signature verification fields."""
    status = server_status()
    assert "dataset_signature_verified" in status
    assert status["dataset_signature_verified"] is True
    assert "datasets" in status

    for name in DATASET_CONFIG:
        assert name in status["datasets"]
        meta = status["datasets"][name]
        assert meta["verified"] is True
        assert meta["key_id"] == "mcp-india-stack-ed25519-primary"
        assert meta["version"] == 20250401
        assert meta["age_days"] is not None


def test_cli_verify_data_success() -> None:
    """CLI --verify-data command exits 0 and prints verification table."""
    cmd = [sys.executable, "-m", "mcp_india_stack.server", "--verify-data"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[PASS] ifsc" in res.stdout
    assert "[PASS] pincode" in res.stdout
    assert "[PASS] hsn" in res.stdout
    assert "All dataset signatures and checksums verified successfully" in res.stdout


def test_cli_verify_data_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI --verify-data exits 1 when a dataset or cache fails verification."""
    # Write corrupt cache file with no manifest
    cache_dir = tmp_path / "corrupt_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "IFSC.csv").write_bytes(b"tampered content")

    import os

    test_env = os.environ.copy()
    test_env["MCP_INDIA_STACK_CACHE_DIR"] = str(cache_dir)

    cmd = [sys.executable, "-m", "mcp_india_stack.server", "--verify-data"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=test_env)
    assert res.returncode == 1
    assert "FAIL" in res.stdout or "FAIL" in res.stderr
