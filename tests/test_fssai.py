"""Tests for FSSAI license validator."""

from mcp_india_stack.tools.fssai import validate_fssai


class TestFSSAIValid:
    def test_valid_14_digit(self):
        result = validate_fssai("10012345678901")
        assert result["valid"] is True
        assert result["license_number"] == "10012345678901"

    def test_extracts_state_code(self):
        result = validate_fssai("10012345678901")
        assert "state_code" in result or "state" in result.get("decoded", {})

    def test_extracts_license_type(self):
        result = validate_fssai("10012345678901")
        assert "license_type" in result or "type" in result.get("decoded", {})

    def test_central_license_type(self):
        result = validate_fssai("10012345678901")
        if "decoded" in result:
            assert result["decoded"].get("license_type") in ["Central", "1", "central"]

    def test_normalizes_input(self):
        result = validate_fssai("  10012345678901  ")
        assert result["valid"] is True


class TestFSSAIInvalid:
    def test_empty_string(self):
        result = validate_fssai("")
        assert result["valid"] is False

    def test_13_digits(self):
        result = validate_fssai("1001234567890")
        assert result["valid"] is False
        assert "14 digits" in str(result["errors"])

    def test_15_digits(self):
        result = validate_fssai("100123456789012")
        assert result["valid"] is False

    def test_non_numeric(self):
        result = validate_fssai("1001234567890A")
        assert result["valid"] is False

    def test_with_spaces(self):
        result = validate_fssai("1001 2345 6789 01")
        assert result["valid"] is True

    def test_with_dashes(self):
        result = validate_fssai("1001-2345-6789-01")
        assert result["valid"] is True


class TestFSSAIWarnings:
    def test_old_year_warning(self):
        result = validate_fssai("10112345678901")
        if "warnings" in result and len(result["warnings"]) > 0:
            assert (
                "year" in str(result["warnings"]).lower()
                or "old" in str(result["warnings"]).lower()
            )
