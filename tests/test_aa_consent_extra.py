from mcp_india_stack.tools.aa_consent_validate import validate_aa_consent_artifact


def test_aa_consent_validate_invalid_branches():
    r = validate_aa_consent_artifact(
        {"status": "UNKNOWN", "createTimestamp": "bad_format", "signedConsent": ""}
    )
    assert r["structurally_valid"] is False
