"""AA consent artifact validator - offline structural validation."""

from __future__ import annotations

from typing import Any

VALID_STATUSES = ["ACTIVE", "PAUSED", "REVOKED", "EXPIRED"]

DISCLAIMER = (
    "Structural validation only. Signature verification and active status "
    "must be confirmed with the AA operator."
)


def validate_aa_consent_artifact(consent_artifact: dict[str, Any]) -> dict[str, Any]:
    """Validate consent artifact structure per ReBIT spec.

    Args:
        consent_artifact: The consent artifact JSON from AA

    Returns:
        Dict with field-level validation results.
    """
    errors: list[str] = []
    warnings: list[str] = []

    required_fields = [
        "id",
        "ver",
        "txnid",
        "consentId",
        "status",
        "createTimestamp",
        "signedConsent",
    ]
    field_checks: dict[str, str] = {}

    for field in required_fields:
        if field in consent_artifact and consent_artifact[field]:
            field_checks[field] = "present"
        else:
            field_checks[field] = "missing"
            errors.append(f"Missing required field: {field}")

    if "status" in consent_artifact:
        status = consent_artifact["status"]
        if status in VALID_STATUSES:
            field_checks["status"] = "valid_value"
        else:
            field_checks["status"] = "invalid_value"
            errors.append(f"Invalid status '{status}'. Valid: {VALID_STATUSES}")
    else:
        field_checks["status"] = "missing"

    if "createTimestamp" in consent_artifact:
        ts = consent_artifact["createTimestamp"]
        if isinstance(ts, str) and "T" in ts:
            field_checks["createTimestamp"] = "valid_iso8601"
        else:
            field_checks["createTimestamp"] = "invalid_format"
    else:
        field_checks["createTimestamp"] = "missing"

    if "signedConsent" in consent_artifact:
        if consent_artifact["signedConsent"]:
            field_checks["signedConsent"] = "present_not_verified"
            warnings.append(
                "signedConsent cryptographic verification requires AA's JWK endpoint"
                " — not performed offline"
            )
        else:
            field_checks["signedConsent"] = "present_but_empty"

    structurally_valid = len(errors) == 0

    return {
        "structurally_valid": structurally_valid,
        "status": consent_artifact.get("status", "unknown"),
        "consent_id": consent_artifact.get("consentId", ""),
        "field_checks": field_checks,
        "warnings": warnings,
        "errors": errors,
        "disclaimer": DISCLAIMER,
    }
