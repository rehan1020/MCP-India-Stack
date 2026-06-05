"""Tests for AA consent artifact validator."""

from mcp_india_stack.tools.aa_consent_validate import validate_aa_consent_artifact

VALID = {
    "id": "req-001",
    "ver": "2.0",
    "txnid": "txn-abc-123",
    "consentId": "consent-uuid-001",
    "status": "ACTIVE",
    "createTimestamp": "2025-05-01T10:00:00Z",
    "signedConsent": "eyJhbGciOiJSUzI1NiJ9.payload.signature",
}


def test_valid_active_consent():
    result = validate_aa_consent_artifact(VALID)
    assert result.get("structurally_valid") is True
    assert result.get("status") == "ACTIVE"
    assert len(result.get("errors", [])) == 0


def test_all_valid_statuses():
    for status in ["ACTIVE", "PAUSED", "REVOKED", "EXPIRED"]:
        result = validate_aa_consent_artifact({**VALID, "status": status})
        assert result.get("field_checks", {}).get("status") == "valid_value"


def test_missing_consent_id():
    art = {k: v for k, v in VALID.items() if k != "consentId"}
    result = validate_aa_consent_artifact(art)
    assert result.get("structurally_valid") is False
    assert any("consentId" in e for e in result.get("errors", []))


def test_invalid_status_value():
    result = validate_aa_consent_artifact({**VALID, "status": "UNKNOWN"})
    assert result.get("field_checks", {}).get("status") == "invalid_value"
    assert len(result.get("errors", [])) > 0


def test_missing_signed_consent():
    art = {k: v for k, v in VALID.items() if k != "signedConsent"}
    result = validate_aa_consent_artifact(art)
    assert result.get("field_checks", {}).get("signedConsent") == "missing"


def test_signature_verification_warning():
    result = validate_aa_consent_artifact(VALID)
    assert any(
        "signature" in w.lower() or "cryptographic" in w.lower() for w in result.get("warnings", [])
    )


def test_missing_txnid():
    art = {k: v for k, v in VALID.items() if k != "txnid"}
    result = validate_aa_consent_artifact(art)
    assert result.get("structurally_valid") is False
