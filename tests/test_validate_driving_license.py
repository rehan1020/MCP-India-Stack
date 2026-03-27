"""Tests for Driving License validation."""

from mcp_india_stack.tools.driving_license import validate_driving_license


class TestValidFormat:
    def test_standard_15_char(self) -> None:
        result = validate_driving_license("MH0220191234567")
        assert result["valid"] is True
        assert result["state_code"] == "MH"
        assert result["state_name"] == "Maharashtra"
        assert result["rto_code"] == "02"
        assert result["year_of_issue"] == "2019"
        assert result["serial"] == "1234567"

    def test_delhi_dl(self) -> None:
        result = validate_driving_license("DL0520189876543")
        assert result["valid"] is True
        assert result["state_code"] == "DL"
        assert result["state_name"] == "Delhi"


class TestNonStandard:
    def test_13_char_alphanumeric_warns(self) -> None:
        result = validate_driving_license("MH02201912345")
        assert result["valid"] is False
        errors_str = str(result["errors"]).lower()
        assert "pre-sarathi" in errors_str or "non-standard" in errors_str

    def test_too_short(self) -> None:
        result = validate_driving_license("MH020201")
        assert result["valid"] is False


class TestStateCodeDecode:
    def test_unknown_state_code(self) -> None:
        result = validate_driving_license("ZZ0220191234567")
        assert result["valid"] is False
        assert "Unrecognised" in str(result["errors"])


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = validate_driving_license("MH0220191234567")
        assert "disclaimer" in result
