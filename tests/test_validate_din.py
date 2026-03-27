"""Tests for DIN validation."""

from mcp_india_stack.tools.din import validate_din


class TestValidDIN:
    def test_valid_8_digits(self) -> None:
        result = validate_din("00012345")
        assert result["valid"] is True
        assert result["din"] == "00012345"

    def test_zero_padded(self) -> None:
        """Short input gets zero-padded to 8 digits."""
        result = validate_din("12345")
        assert result["valid"] is True
        assert result["din"] == "00012345"


class TestInvalidDIN:
    def test_non_numeric(self) -> None:
        result = validate_din("0001234A")
        assert result["valid"] is False

    def test_too_long(self) -> None:
        result = validate_din("123456789")
        assert result["valid"] is False

    def test_empty(self) -> None:
        result = validate_din("")
        assert result["valid"] is False


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = validate_din("00012345")
        assert "disclaimer" in result
        assert "MCA" in str(result["disclaimer"])


class TestEdgeCases:
    def test_none_input(self) -> None:
        result = validate_din(None)  # type: ignore[arg-type]
        assert result["valid"] is False
        assert "required" in str(result["errors"]).lower()

    def test_whitespace_only(self) -> None:
        result = validate_din("   ")
        assert result["valid"] is False
        assert "empty" in str(result["errors"]).lower()

    def test_all_zeros(self) -> None:
        result = validate_din("00000000")
        assert result["valid"] is True
        assert result["din"] == "00000000"
