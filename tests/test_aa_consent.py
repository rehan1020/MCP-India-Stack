"""Tests for AA consent request builder."""

from mcp_india_stack.tools.aa_consent import build_aa_consent_request


def test_onetime_deposit_consent():
    result = build_aa_consent_request(
        customer_id="user@onemoney",
        fi_types=["DEPOSIT"],
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
        fetch_type="ONETIME",
    )
    assert result.get("valid") is True
    payload = result.get("consent_request_payload", {})
    assert "DEPOSIT" in payload.get("fiTypes", [])
    assert payload.get("fetchType") == "ONETIME"
    assert payload.get("consentMode") == "VIEW"


def test_periodic_consent_with_frequency():
    result = build_aa_consent_request(
        customer_id="user@finvu",
        fi_types=["MUTUAL_FUNDS"],
        date_range_from="2025-01-01",
        date_range_to="2025-12-31",
        fetch_type="PERIODIC",
        frequency_unit="MONTH",
        frequency_value=1,
    )
    assert result.get("valid") is True
    payload = result.get("consent_request_payload", {})
    assert "Frequency" in payload


def test_all_fi_types_valid():
    valid = [
        "DEPOSIT",
        "MUTUAL_FUNDS",
        "INSURANCE",
        "NPS",
        "EQUITIES",
        "GSTIN_DATA",
        "CREDIT_CARD",
        "RECURRING_DEPOSIT",
    ]
    result = build_aa_consent_request(
        customer_id="test@aa",
        fi_types=valid,
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
    )
    assert result.get("valid") is True


def test_date_range_reversed():
    result = build_aa_consent_request(
        customer_id="user@aa",
        fi_types=["DEPOSIT"],
        date_range_from="2026-03-31",
        date_range_to="2025-04-01",
    )
    assert result.get("valid") is False


def test_invalid_fi_type():
    result = build_aa_consent_request(
        customer_id="user@aa",
        fi_types=["INVALID"],
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
    )
    assert result.get("valid") is False


def test_periodic_missing_frequency():
    result = build_aa_consent_request(
        customer_id="user@aa",
        fi_types=["DEPOSIT"],
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
        fetch_type="PERIODIC",
    )
    assert result.get("valid") is False


def test_consent_expiry_in_payload():
    result = build_aa_consent_request(
        customer_id="user@aa",
        fi_types=["DEPOSIT"],
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
        consent_expiry_days=30,
    )
    assert result.get("valid") is True
    payload = result.get("consent_request_payload", {})
    assert "consentStart" in payload
    assert "consentExpiry" in payload


def test_next_step_note_in_response():
    result = build_aa_consent_request(
        customer_id="user@aa",
        fi_types=["DEPOSIT"],
        date_range_from="2025-04-01",
        date_range_to="2026-03-31",
    )
    assert result.get("valid") is True
    assert "next_step" in result
