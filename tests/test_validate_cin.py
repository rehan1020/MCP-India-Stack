"""Tests for CIN validation."""

from mcp_india_stack.tools.cin import validate_cin


class TestRealCIN:
    def test_reliance_cin(self) -> None:
        """Real CIN from MCA21 — Reliance Industries."""
        result = validate_cin("L17110MH1973PLC019786")
        assert result["valid"] is True
        assert result["listing_status"] == "Listed"
        assert result["nic_code"] == "17110"
        assert result["state_code"] == "MH"
        assert result["state_name"] == "Maharashtra"
        assert result["year_of_incorporation"] == "1973"
        assert result["company_type_code"] == "PLC"
        assert result["company_type"] == "Public Limited Company"
        assert result["sequential_number"] == "019786"


class TestListingStatus:
    def test_listed(self) -> None:
        result = validate_cin("L17110MH1973PLC019786")
        assert result["listing_status"] == "Listed"

    def test_unlisted(self) -> None:
        result = validate_cin("U72200MH2007PTC175696")
        assert result["valid"] is True
        assert result["listing_status"] == "Unlisted"


class TestCompanyTypes:
    def test_plc(self) -> None:
        result = validate_cin("L17110MH1973PLC019786")
        assert result["company_type"] == "Public Limited Company"

    def test_ptc(self) -> None:
        result = validate_cin("U72200MH2007PTC175696")
        assert result["company_type"] == "Private Limited Company"

    def test_flc(self) -> None:
        result = validate_cin("U72200MH2007FLC175696")
        assert result["company_type"] == "Foreign Company"

    def test_goi(self) -> None:
        result = validate_cin("U72200MH2007GOI175696")
        assert result["company_type"] == "Government Company"

    def test_npl(self) -> None:
        result = validate_cin("U72200MH2007NPL175696")
        assert result["company_type"] == "Not for Profit License Company"

    def test_opc(self) -> None:
        result = validate_cin("U72200MH2007OPC175696")
        assert result["company_type"] == "One Person Company"

    def test_ulc(self) -> None:
        result = validate_cin("U72200MH2007ULC175696")
        assert result["company_type"] == "Unlimited Liability Company"


class TestInvalidLength:
    def test_20_chars(self) -> None:
        result = validate_cin("L17110MH1973PLC01978")
        assert result["valid"] is False
        assert "21 characters" in str(result["errors"])

    def test_22_chars(self) -> None:
        result = validate_cin("L17110MH1973PLC0197861")
        assert result["valid"] is False
        assert "21 characters" in str(result["errors"])


class TestEmptyInput:
    def test_empty_string(self) -> None:
        result = validate_cin("")
        assert result["valid"] is False

    def test_none_input(self) -> None:
        result = validate_cin(None)  # type: ignore[arg-type]
        assert result["valid"] is False
        assert "required" in str(result["errors"]).lower()


class TestRegexFail:
    def test_21_chars_but_bad_format(self) -> None:
        """21 chars that pass length check but fail CIN regex."""
        result = validate_cin("X17110MH1973PLC019786")  # starts with X, not L/U
        assert result["valid"] is False
        assert "format is invalid" in str(result["errors"]).lower()


class TestFieldWarnings:
    def test_unknown_state_code(self) -> None:
        """Valid structure but unrecognised state code ZZ."""
        result = validate_cin("L17110ZZ1973PLC019786")
        assert "Unrecognised state code" in str(result["errors"])
        assert result["valid"] is False

    def test_unknown_company_type(self) -> None:
        """Valid structure but unrecognised company type XYZ."""
        result = validate_cin("L17110MH1973XYZ019786")
        assert "Unrecognised company type" in str(result["errors"])
        assert result["valid"] is False

    def test_implausible_year(self) -> None:
        """Year 1800 — out of plausible range."""
        result = validate_cin("L17110MH1800PLC019786")
        assert "out of plausible range" in str(result["errors"])
        assert result["valid"] is False
