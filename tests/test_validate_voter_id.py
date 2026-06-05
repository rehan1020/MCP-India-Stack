"""Tests for Voter ID (EPIC) validation."""

from mcp_india_stack.tools.voter_id import validate_voter_id


class TestValidFormat:
    def test_standard_format(self) -> None:
        result = validate_voter_id("ABC1234567")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["prefix"] == "ABC"
        assert result["data"]["serial"] == "1234567"
        assert result["data"]["format"] == "standard"

    def test_lowercase_normalised(self) -> None:
        result = validate_voter_id("abc1234567")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["epic"] == "ABC1234567"


class TestInvalidLength:
    def test_9_chars_invalid(self) -> None:
        result = validate_voter_id("ABC123456")
        assert result["success"] is False
        assert result["data"]["valid"] is False

    def test_11_chars_invalid(self) -> None:
        result = validate_voter_id("ABC12345678")
        assert result["success"] is False
        assert result["data"]["valid"] is False


class TestAllDigits:
    def test_all_digits_invalid(self) -> None:
        result = validate_voter_id("1234567890")
        assert result["success"] is False
        assert result["data"]["valid"] is False


class TestLegacyFormat:
    def test_legacy_format_detected(self) -> None:
        result = validate_voter_id("AB12CD5678")
        assert result["success"] is False
        assert result["data"]["valid"] is False
        assert result["data"]["format"] == "legacy_possible"
        assert "legacy" in str(result["errors"]).lower()


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = validate_voter_id("ABC1234567")
        assert "disclaimer" not in result or "disclaimer" in result.get("data", {})


class TestEdgeCases:
    def test_none_input(self) -> None:
        result = validate_voter_id(None)  # type: ignore[arg-type]
        assert result["success"] is False
        assert result["data"]["valid"] is False
        assert "required" in str(result["errors"]).lower()

    def test_empty_string(self) -> None:
        result = validate_voter_id("")
        assert result["success"] is False
        assert result["data"]["valid"] is False
        assert "empty" in str(result["errors"]).lower()

    def test_10_char_wrong_pattern(self) -> None:
        result = validate_voter_id("AB@#$%6789")
        assert result["success"] is False
        assert result["data"]["valid"] is False
        assert result["data"]["format"] == ""
        assert "3 uppercase letters" in str(result["errors"])
