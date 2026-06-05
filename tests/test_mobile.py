"""Tests for mobile number validator."""

import pytest

from mcp_india_stack.tools.mobile import validate_mobile_number


class TestMobileValid:
    def test_valid_10_digits(self):
        result = validate_mobile_number("9821123456")
        assert result["valid"] is True
        assert result["normalized"] == "9821123456"

    def test_with_plus91(self):
        result = validate_mobile_number("+919821123456")
        assert result["valid"] is True

    def test_jio_operator(self):
        result = validate_mobile_number("9821123456")
        assert result["valid"] is True
        assert result["operator"] == "Jio"

    def test_airtel_operator(self):
        result = validate_mobile_number("9841123456")
        assert result["valid"] is True
        assert result["operator"] == "Airtel"

    def test_vodafone_operator(self):
        result = validate_mobile_number("9851123456")
        assert result["valid"] is True
        assert result["operator"] == "Vodafone"

    def test_bsnl_operator(self):
        result = validate_mobile_number("9861123456")
        assert result["valid"] is True
        assert result["operator"] == "BSNL"

    def test_formatted_e164(self):
        result = validate_mobile_number("9821123456")
        assert "formatted_e164" in result


class TestMobileInvalid:
    def test_9_digits(self):
        result = validate_mobile_number("982012345")
        assert result["valid"] is False

    def test_11_digits(self):
        result = validate_mobile_number("98211234567")
        assert result["valid"] is False

    def test_starts_with_5(self):
        result = validate_mobile_number("5821123456")
        assert result["valid"] is False

    def test_with_letters(self):
        result = validate_mobile_number("9821ABC456")
        assert result["valid"] is False

    def test_empty_string(self):
        result = validate_mobile_number("")
        assert result["valid"] is False

    def test_unknown_prefix(self):
        result = validate_mobile_number("9991123456")
        assert result["valid"] is True
        assert result["operator"] == "Unknown"


# --- Fix 2: All mobile format tests ---


@pytest.mark.parametrize(
    "mobile",
    [
        "9212102919",
        "+919212102919",
        "919212102919",
        "09212102919",
        "9212 102919",
        "9212-102919",
    ],
)
def test_mobile_all_formats_valid(mobile):
    result = validate_mobile_number(mobile)
    assert result["valid"] is True, f"Expected valid for {mobile!r}, got: {result}"


def test_mobile_11_raw_digits_invalid():
    """Genuinely 11 digits (not a country code prefix) should be invalid."""
    result = validate_mobile_number("92121029190")
    assert result["valid"] is False
    assert "10 digits" in result["error"]


def test_mobile_number_with_zeros_preserved():
    """Numbers with interior zeros must be preserved correctly."""
    result = validate_mobile_number("9000000001")
    assert result["valid"] is True
    assert result["normalized"] == "9000000001"
