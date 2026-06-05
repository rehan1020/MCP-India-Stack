"""Tests for PRAN (Permanent Retirement Account Number) validator."""

from mcp_india_stack.tools.pran import validate_pran


def test_pran_valid_apy():
    result = validate_pran("400123456789")
    assert result["valid"] is True
    assert "Atal" in result["subscriber_category"] or "APY" in result["subscriber_category"]


def test_pran_valid_corporate():
    result = validate_pran("300123456789")
    assert result["valid"] is True
    assert (
        "Corporate" in result["subscriber_category"]
        or "private" in result["subscriber_category"].lower()
    )


def test_pran_central_govt():
    result = validate_pran("100123456789")
    assert result["valid"] is True
    assert (
        "Central" in result["subscriber_category"] or "Government" in result["subscriber_category"]
    )


def test_pran_state_govt():
    result = validate_pran("200123456789")
    assert result["valid"] is True


def test_pran_nps_lite():
    result = validate_pran("500123456789")
    assert result["valid"] is True


def test_pran_with_spaces():
    result = validate_pran("4001 2345 6789")
    assert result["valid"] is True


def test_pran_11_digits():
    result = validate_pran("40012345678")
    assert result["valid"] is False
    assert "error" in result


def test_pran_13_digits():
    result = validate_pran("4001234567890")
    assert result["valid"] is False


def test_pran_with_letters():
    result = validate_pran("40012ABC6789")
    assert result["valid"] is False


def test_pran_empty():
    result = validate_pran("")
    assert result["valid"] is False
