"""Tests for AA FI type decoder."""

from mcp_india_stack.tools.aa_fi_type import decode_aa_fi_type


def test_deposit_fi_type():
    result = decode_aa_fi_type("DEPOSIT")
    assert result.get("fi_type") == "DEPOSIT"
    assert (
        "bank" in result.get("description", "").lower()
        or "deposit" in result.get("description", "").lower()
    )


def test_equities_has_tool_pairing():
    result = decode_aa_fi_type("EQUITIES")
    assert result.get("mcp_tool_pairing") is not None
    assert "capital_gains" in result.get("mcp_tool_pairing", "")


def test_gstin_data_pairing():
    result = decode_aa_fi_type("GSTIN_DATA")
    assert "validate_gstin" in result.get("mcp_tool_pairing", "")


def test_all_fi_types_decode():
    for fi_type in [
        "DEPOSIT",
        "MUTUAL_FUNDS",
        "INSURANCE",
        "NPS",
        "EQUITIES",
        "GSTIN_DATA",
        "CREDIT_CARD",
        "RECURRING_DEPOSIT",
    ]:
        result = decode_aa_fi_type(fi_type)
        assert result.get("fi_type") == fi_type
        assert "description" in result


def test_typical_fields_is_list():
    result = decode_aa_fi_type("DEPOSIT")
    assert isinstance(result.get("typical_fields"), list)
    assert len(result.get("typical_fields", [])) > 0


def test_invalid_fi_type():
    result = decode_aa_fi_type("INVALID_TYPE")
    assert "error" in result


def test_case_insensitive():
    result = decode_aa_fi_type("deposit")
    assert result.get("fi_type") == "DEPOSIT"


def test_nps_has_pran_in_fields():
    result = decode_aa_fi_type("NPS")
    fields_str = str(result.get("typical_fields", [])).lower()
    assert "pran" in fields_str or "pension" in fields_str
