"""Tests for ISIN (International Securities Identification Number) decoder."""

import pytest

from mcp_india_stack.tools.isin import decode_isin


def test_isin_valid_indian():
    result = decode_isin("INE002A01018")
    assert result["country_code"] == "IN"
    assert result["country"] == "India"
    assert "security_type" in result


def test_isin_nsin_extracted():
    result = decode_isin("INE002A01018")
    assert result["nsin"] == "E002A01018"


def test_isin_equity_security_type():
    result = decode_isin("INE002A01018")
    assert "equity" in result["security_type"].lower() or "share" in result["security_type"].lower()


def test_isin_check_digit():
    result = decode_isin("INE002A01018")
    assert "checksum_valid" in result


def test_isin_lowercase_normalized():
    result = decode_isin("ine002a01018")
    assert result["isin"] == "INE002A01018"


def test_isin_with_spaces_stripped():
    result = decode_isin("  INE002A01018  ")
    assert result["isin"] == "INE002A01018"


def test_isin_invalid_checksum():
    result = decode_isin("INE002A01019")
    assert result["checksum_valid"] is False


def test_isin_wrong_length_short():
    result = decode_isin("INE002A010")
    assert result["valid"] is False


def test_isin_wrong_length_long():
    result = decode_isin("INE002A010181")
    assert result["valid"] is False


def test_isin_empty():
    result = decode_isin("")
    assert result["valid"] is False


def test_isin_non_indian_still_parses():
    result = decode_isin("US0231351067")
    assert result["country_code"] == "US"


# --- Bug fix verification tests ---


@pytest.mark.parametrize(
    "isin",
    [
        "INE002A01018",  # Reliance Industries
        "INE040A01034",  # HDFC Bank
        "INE009A01021",  # Infosys
        "US0378331005",  # Apple (non-India, for format test)
    ],
)
def test_isin_known_valid(isin):
    result = decode_isin(isin)
    assert result["checksum_valid"] is True, f"Expected valid for {isin}"


def test_isin_tampered_checksum():
    """Last digit changed from 8 to 9 should fail checksum."""
    result = decode_isin("INE002A01019")
    assert result["checksum_valid"] is False
