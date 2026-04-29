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


class TestEdgeCases:
    def test_dl_unknown_state_code(self) -> None:
        result = validate_driving_license("ZZ2020191234567")
        assert result["state_name"] == "Unknown"

    def test_dl_future_year(self) -> None:
        result = validate_driving_license("MH9921991234567")
        assert "out of plausible range" in str(result["errors"]).lower() or result["valid"] is False

    def test_dl_pre_1990_year(self) -> None:
        result = validate_driving_license("MH0019851234567")
        assert result["valid"] is True

    def test_dl_14_char_format(self) -> None:
        result = validate_driving_license("MH20201234567")
        assert result["valid"] is False

    def test_dl_none_input(self) -> None:
        result = validate_driving_license(None)
        assert result["valid"] is False
        assert "required" in str(result["errors"]).lower()

    def test_dl_hyphenated_input(self) -> None:
        result = validate_driving_license("MH-20-20230000001")
        assert result["valid"] is True
        assert "-" not in result["dl_number"]

    def test_dl_invalid_chars(self) -> None:
        result = validate_driving_license("MH20@2023000001")
        assert result["valid"] is False

    def test_dl_only_hyphens(self) -> None:
        result = validate_driving_license("--")
        assert result["valid"] is False
        assert "empty" in str(result["errors"]).lower()
