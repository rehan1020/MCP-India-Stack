"""Data models and core semantics for the MCP India Stack Authenticity System.

Defines attestation levels (A0-A4), authenticity checks, evidence hashing,
and evaluation rules (R1-R6).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from mcp_india_stack.logging_filter import mask_aadhaar_text

# Canonical attestation levels
LEVEL_ORDER: tuple[str, ...] = ("A0", "A1", "A2", "A3", "A4")

AUTHENTICITY_SCHEMA: dict[str, Any] = {
    "type": ["object", "null"],
    "properties": {
        "level": {"type": ["string", "null"], "enum": ["A0", "A1", "A2", "A3", "A4", None]},
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "level": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["name", "passed", "level", "detail"],
            },
        },
        "source": {"type": "string"},
        "dataset_version": {"type": ["string", "null"]},
        "as_of": {"type": "string"},
        "evidence_hash": {"type": ["string", "null"]},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "registry_status": {"type": "string"},
    },
    "required": ["level", "checks", "source", "as_of", "limitations"],
}

AUTHENTICITY_SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "A0": {"type": "integer"},
                "A1": {"type": "integer"},
                "A2": {"type": "integer"},
                "A3": {"type": "integer"},
                "A4": {"type": "integer"},
                "null": {"type": "integer"},
            },
        }
    },
    "required": ["summary"],
}

# Low-entropy keys prohibited from evidence hashing (Rule R4)
_LOW_ENTROPY_KEY_PATTERN = re.compile(
    r"^(aadhaar|pan|vpa|upi|mobile|phone|identifier|voter_id|passport|account_number)",
    re.IGNORECASE,
)
_AADHAAR_RE = re.compile(r"^\d{12}$")
_PAN_RE = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")
_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


@dataclass(frozen=True)
class AuthenticityCheck:
    """Individual verification or attestation check."""

    name: str
    passed: bool
    level: str  # "A0", "A1", "A2", "A3", "A4"
    detail: str

    def to_dict(self) -> dict[str, Any]:
        """Convert check to dictionary with PII redaction applied (Rule R6)."""
        return {
            "name": self.name,
            "passed": self.passed,
            "level": self.level,
            "detail": mask_aadhaar_text(self.detail),
        }


def compute_evidence_hash(record: dict[str, Any] | None) -> str | None:
    """Compute deterministic SHA-256 digest of a public authoritative dataset record.

    Enforces Rule R4:
    Never emit a hash or digest of a low-entropy identifier (Aadhaar, mobile, PAN, VPA)
    in evidence_hash or anywhere else, as such digests are reversible by enumeration.
    Only normalized public dataset records (e.g. IFSC directory entry, pincode entry,
    state code entry) may be digested.
    """
    if not record or not isinstance(record, dict):
        return None

    # Inspect keys and values for low-entropy identifiers (Rule R4)
    clean_record: dict[str, Any] = {}
    for k, v in record.items():
        if _LOW_ENTROPY_KEY_PATTERN.search(str(k)):
            return None
        v_str = str(v).strip()
        if _AADHAAR_RE.match(v_str) or _PAN_RE.match(v_str) or _MOBILE_RE.match(v_str):
            return None
        # Omit None or empty values from canonical record
        if v is not None:
            clean_record[str(k)] = v

    if not clean_record:
        return None

    try:
        canonical_json = json.dumps(clean_record, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"
    except (TypeError, ValueError):
        return None


def evaluate_level(checks: list[AuthenticityCheck], valid: bool) -> str | None:
    """Evaluate consecutive attestation level from checks list.

    Enforces:
    - Rule R1: level equals the highest consecutive level whose checks all passed.
      It is never inflated.
    - Rule R2: valid=false gives level=null.
    """
    if not valid:
        return None

    if not checks:
        return "A0"

    checks_by_level: dict[str, list[AuthenticityCheck]] = {lvl: [] for lvl in LEVEL_ORDER}
    for check in checks:
        if check.level in checks_by_level:
            checks_by_level[check.level].append(check)

    current_level: str | None = None

    # Must start at A0
    a0_checks = checks_by_level["A0"]
    if a0_checks:
        if not all(c.passed for c in a0_checks):
            return None
        current_level = "A0"
    else:
        # Default baseline if valid
        current_level = "A0"

    # Evaluate consecutive levels in strict order
    for lvl in ("A1", "A2", "A3", "A4"):
        lvl_checks = checks_by_level[lvl]
        if not lvl_checks:
            # If no checks are defined for this level (e.g. A2 dataset lookup is not
            # applicable for artifact signature verification A3), continue evaluating.
            continue
        if all(c.passed for c in lvl_checks):
            current_level = lvl
        else:
            # Check failed at this level; stop advancing
            break

    return current_level


def build_authenticity_envelope(
    *,
    checks: list[AuthenticityCheck],
    valid: bool,
    source: str,
    dataset_version: str | None = None,
    as_of: str | None = None,
    evidence_record: dict[str, Any] | None = None,
    custom_limitations: list[str] | None = None,
    limitations: list[str] | None = None,
    is_dataset_miss: bool = False,
    registry_status: str | None = None,
) -> dict[str, Any]:
    """Construct a complete, standard Authenticity envelope adhering to rules R1-R6."""
    level = evaluate_level(checks, valid)

    # Build limitations list (Rule R6: apply PII redaction)
    collected_limitations: list[str] = []

    # Rule R3: dataset miss is NOT evidence of forgery
    if is_dataset_miss:
        miss_ver = dataset_version or "2025.04"
        collected_limitations.append(f"not_found_in_dataset@{miss_ver}")

    all_custom = (custom_limitations or []) + (limitations or [])
    if all_custom:
        for lim in all_custom:
            collected_limitations.append(mask_aadhaar_text(str(lim)))

    # Ensure limitations is always non-empty below A4
    if level != "A4":
        if not collected_limitations:
            collected_limitations.append("active registration status not verified")
        elif "active registration status not verified" not in collected_limitations:
            # Standard baseline caveat
            collected_limitations.append("active registration status not verified")

    # Evidence hash (Rule R4: only for public dataset records at A2 or above)
    evidence_hash: str | None = None
    if level in ("A2", "A3", "A4") and evidence_record:
        evidence_hash = compute_evidence_hash(evidence_record)

    # as_of date: deterministic string (Rule R5)
    as_of_date = as_of or date.today().isoformat()

    envelope: dict[str, Any] = {
        "level": level,
        "checks": [c.to_dict() for c in checks],
        "source": source,
        "dataset_version": dataset_version,
        "as_of": as_of_date,
        "evidence_hash": evidence_hash,
        "limitations": collected_limitations,
    }

    # registry_status is absent unless A4 (or explicitly provided)
    if registry_status is not None and level == "A4":
        envelope["registry_status"] = registry_status

    return envelope


def summarize_authenticity_levels(items: list[dict[str, Any]]) -> dict[str, int]:
    """Summarize counts of authenticity levels across bulk result items."""
    counts: dict[str, int] = {
        "A0": 0,
        "A1": 0,
        "A2": 0,
        "A3": 0,
        "A4": 0,
        "null": 0,
    }
    for item in items:
        auth = item.get("authenticity")
        if isinstance(auth, dict):
            lvl = auth.get("level")
            if lvl in counts:
                counts[lvl] += 1
            else:
                counts["null"] += 1
        else:
            counts["null"] += 1
    return counts
