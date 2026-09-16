"""Test new modules for coverage."""


class TestPermissionTier:
    def test_enum_values(self) -> None:
        from mcp_india_stack.permission_tiers import PermissionTier

        assert PermissionTier.READ_ONLY == 0
        assert PermissionTier.LOOKUP_LIVE == 1
        assert PermissionTier.INITIATE == 2
        assert PermissionTier.SUBMIT == 3

    def test_enum_members(self) -> None:
        from mcp_india_stack.permission_tiers import PermissionTier

        members = list(PermissionTier)
        assert len(members) == 4


class TestResponses:
    def test_build_response_with_optional_fields(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(
            success=True,
            data={"test": "data"},
            validated_by=["format", "checksum"],
            normalized_input="test123",
            stale=True,
            stale_reason="old_data",
            data_version="1.0",
            rate_limit_remaining=50,
            rate_limit_warning="low",
        )
        assert result["stale"] is True
        assert result["stale_reason"] == "old_data"
        assert result["data_version"] == "1.0"
        assert result["rate_limit_remaining"] == 50
        assert result["rate_limit_warning"] == "low"

    def test_calculate_confidence_various(self) -> None:
        from mcp_india_stack.utils.responses import _calculate_confidence

        assert _calculate_confidence([], True) == 0.0
        assert _calculate_confidence(["format"], True) == 0.4
        assert _calculate_confidence(["format", "checksum"], True) == 0.65
        assert _calculate_confidence(["format", "live_ping"], True) == 0.85
        assert _calculate_confidence(["db_lookup"], True) == 1.0
        assert _calculate_confidence(["format"], False) == 0.0

    def test_build_response_basic(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={"test": True})
        assert result["success"] is True
        assert result["confidence"] == 0.4  # Default confidence

    def test_build_response_with_validated_by(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={}, validated_by=["format", "checksum"])
        assert result["confidence"] == 0.65

    def test_build_response_with_live(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(
            success=True, data={}, validated_by=["format", "checksum", "live_ping"]
        )
        assert result["confidence"] == 0.85

    def test_build_response_failure(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=False, errors=["test error"])
        assert result["confidence"] == 0.0

    def test_build_response_with_normalized_input(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={}, normalized_input="TEST123")
        assert result["normalized_input"] == "TEST123"


class TestNormalization:
    def test_normalize_gstin(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        result = normalize_gstin("27 AAPFU 0939F 1ZV")
        assert result["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_pan(self) -> None:
        from mcp_india_stack.normalization import normalize_pan

        result = normalize_pan("aapfu0939f")
        assert result["normalized_input"] == "AAPFU0939F"

    def test_normalize_ifsc(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        result = normalize_ifsc("SBIN 0001234")
        assert result["normalized_input"] == "SBIN0001234"

    def test_normalize_aadhaar(self) -> None:
        from mcp_india_stack.normalization import normalize_aadhaar

        result = normalize_aadhaar("1234 5678 9012")
        assert result["normalized_input"] == "123456789012"

    def test_normalize_pincode(self) -> None:
        from mcp_india_stack.normalization import normalize_pincode

        result = normalize_pincode("400 001")
        assert result["normalized_input"] == "400001"

    def test_normalize_cin(self) -> None:
        from mcp_india_stack.normalization import normalize_cin

        result = normalize_cin("U67190TN2014PTC096249")
        assert result["normalized_input"] == "U67190TN2014PTC096249"

    def test_normalize_fssai(self) -> None:
        from mcp_india_stack.normalization import normalize_fssai

        result = normalize_fssai("11223344556677")
        assert result["normalized_input"] == "11223344556677"

    def test_normalize_upi(self) -> None:
        from mcp_india_stack.normalization import normalize_upi

        result = normalize_upi("test@okicici")
        assert result["normalized_input"] == "test@okicici"

    def test_normalize_gstin_strips_spaces(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        assert normalize_gstin("27 aapfu 0939f 1zv")["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_gstin_strips_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        assert normalize_gstin("27-AAPFU-0939F-1ZV")["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_ifsc_strips_spaces(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        assert normalize_ifsc("SBIN 0001234")["normalized_input"] == "SBIN0001234"

    def test_normalize_ifsc_strips_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        assert normalize_ifsc("SBIN-0001234")["normalized_input"] == "SBIN0001234"

    def test_normalize_upi_strips_spaces_not_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_upi

        assert normalize_upi("test user@okicici")["normalized_input"] == "testuser@okicici"
        assert normalize_upi("test-user@okicici")["normalized_input"] == "test-user@okicici"


class TestFssaiTool:
    def test_validate_fssai_valid(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11223344556677")
        assert result["valid"] is True
        assert "state_code" in result

    def test_validate_fssai_invalid(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("123")
        assert result["valid"] is False

    def test_validate_fssai_empty(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("")
        assert result["valid"] is False

    def test_validate_fssai_none(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai(None)
        assert result["valid"] is False

    def test_validate_fssai_whitespace_only(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("   ")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_fssai_invalid_state_code(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("50223344556677")
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_validate_fssai_invalid_year_code(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11990012345678")
        assert result["warnings"] or result["valid"] is True

    def test_validate_fssai_non_numeric(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("1122ABCD556677")
        assert result["valid"] is False

    def test_validate_fssai_year_warning(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11319912345678")
        assert "Unusual license year" in result["warnings"][0]


class TestHraTool:
    def test_hra_exemption_metro(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 180000, 240000, "metro")
        assert result["exemption"] > 0

    def test_hra_exemption_non_metro(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(30000, 72000, 120000, "non_metro")
        assert result["exemption"] >= 0

    def test_hra_government(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 100000, 150000, is_government_employee=True)
        assert result["exemption"] >= 0

    def test_hra_invalid(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(-1000, 1000, 500)
        assert "must be positive" in str(result["errors"])

    def test_hra_no_rent(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 180000, 0)
        assert result["exemption"] == 0

    def test_hra_monthly_structure(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_for_salary_structure

        result = calculate_hra_for_salary_structure(50000, 15000, 20000, "Mumbai")
        assert "monthly_exemption" in result


class TestCapitalGainsTool:
    def test_capital_gains_equity_stcg(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(150000, 100000, "equity", 300)
        assert result["short_term_gains"] == 50000
        assert result["tax_liability"] > 0

    def test_capital_gains_equity_ltcg(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(150000, 100000, "equity", 400)
        assert result["long_term_gains"] == 50000

    def test_capital_gains_real_estate(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(2000000, 1000000, "real_estate", 800)
        assert result["is_long_term"] is True

    def test_capital_gains_negative(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(-100000, 50000, "equity")
        assert "cannot be negative" in str(result["errors"])

    def test_home_loan_savings(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_home_loan_savings

        result = calculate_home_loan_savings(2000000, 1000000, 500000, 500)
        assert "capital_gains" in result

    def test_capital_gains_gold(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(200000, 100000, "gold", 400)
        assert result["asset_type"] == "gold"

    def test_capital_gains_crypto(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(200000, 100000, "crypto", 200)
        assert "Cryptocurrency" in result["warnings"][0]

    def test_capital_gains_with_indexation(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            5000000,
            2000000,
            "real_estate",
            700,
            inflation_index_purchase=300,
            inflation_index_sale=350,
        )
        assert result["cost_inflation_adjusted"] > 2000000

    def test_ltcg_equity_below_exemption_threshold_zero_tax(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=400
        )
        assert result["gain_type"] == "LTCG"
        assert result["tax_liability"] == 0.0
        assert result["exemption_applied"] == 25000.0
        assert result["taxable_gain"] == 0.0
        assert "exemption_note" in result

    def test_ltcg_equity_above_exemption_threshold_partial_tax(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=300, quantity=1000, holding_days=400
        )
        assert result["gain_type"] == "LTCG"
        assert result["taxable_gain"] == 75000.0
        assert result["tax_liability"] == 9375.0
        assert result["exemption_applied"] == 125000.0

    def test_ltcg_real_estate_no_exemption_applied(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="real_estate",
            buy_price=5000000,
            sell_price=6000000,
            quantity=1,
            holding_days=800,
        )
        assert result["gain_type"] == "LTCG"
        assert result["exemption_applied"] == 0.0
        assert result["tax_liability"] == result["taxable_gain"] * 0.20

    def test_stcg_equity_no_exemption_applied(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=200
        )
        assert result["gain_type"] == "STCG"
        assert result["exemption_applied"] == 0.0
        assert result["tax_liability"] == 25000 * 0.20

    def test_ltcg_exemption_note_always_present_for_equity(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=400
        )
        assert "exemption_note" in result
        assert "1,25,000" in result["exemption_note"] or "125000" in result["exemption_note"]


class TestAdvanceTaxTool:
    def test_advance_tax_normal(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(estimated_income=1500000)
        assert "installments" in result
        assert len(result["installments"]) == 4

    def test_advance_tax_zero_income(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(estimated_income=0)
        assert result["advance_tax_due"] == 0

    def test_advance_tax_negative(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(estimated_income=-1000)
        assert "must be positive" in str(result["errors"])

    def test_interest_penalty(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_interest_penalty

        result = calculate_interest_penalty(10000, 30)
        assert "interest_penalty" in result

    def test_interest_penalty_negative(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_interest_penalty

        result = calculate_interest_penalty(-1000, 30)
        assert "cannot be negative" in str(result["errors"])


class TestBbpsTool:
    def test_bbps_by_category(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity")
        assert "billers" in result

    def test_bbps_by_state(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity", state="Maharashtra")
        assert "billers" in result

    def test_bbps_by_biller_id(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(biller_id="ELEC_MH_MSEDC")
        assert "billers" in result

    def test_bbps_invalid_category(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="invalid_category")
        assert "errors" in result

    def test_bbps_all_categories(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller()
        assert "categories" in result
