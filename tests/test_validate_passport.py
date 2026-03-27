"""Tests for Passport number validation."""

from mcp_india_stack.tools.passport import validate_passport


class TestValidFormat:
    def test_valid_passport(self) -> None:
        result = validate_passport("A1234567")
        assert result["valid"] is True
        assert result["passport_number"] == "A1234567"
        assert result["series_letter"] == "A"
        assert result["serial"] == "1234567"

    def test_lowercase_normalised(self) -> None:
        result = validate_passport("j9876543")
        assert result["valid"] is True
        assert result["passport_number"] == "J9876543"


class TestInvalidFormat:
    def test_too_short(self) -> None:
        result = validate_passport("A123456")
        assert result["valid"] is False

    def test_too_long(self) -> None:
        result = validate_passport("A12345678")
        assert result["valid"] is False

    def test_all_digits(self) -> None:
        result = validate_passport("12345678")
        assert result["valid"] is False

    def test_all_letters(self) -> None:
        result = validate_passport("ABCDEFGH")
        assert result["valid"] is False


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = validate_passport("A1234567")
        assert "disclaimer" in result
