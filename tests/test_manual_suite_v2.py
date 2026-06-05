"""
Automated test suite — MCP India Stack v0.4.2
Converts all 66 manual test cases into pytest assertions.
All expected values are independently pre-computed.

Run:  pytest tests/test_manual_suite_v2.py -v
CI:   included automatically via testpaths = ["tests"] in pyproject.toml
"""

from __future__ import annotations

import json

import pytest

from mcp_india_stack.tools.aadhaar import validate_aadhaar
from mcp_india_stack.tools.advance_tax import calculate_advance_tax
from mcp_india_stack.tools.capital_gains import calculate_capital_gains
from mcp_india_stack.tools.emi import calculate_emi
from mcp_india_stack.tools.epf_esic import calculate_epf_esic
from mcp_india_stack.tools.fd_maturity import calculate_fd_maturity
from mcp_india_stack.tools.gratuity import calculate_gratuity
from mcp_india_stack.tools.gst_calculator import calculate_gst
from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee
from mcp_india_stack.tools.hra import calculate_hra_exemption, calculate_hra_for_salary_structure
from mcp_india_stack.tools.income_tax import calculate_income_tax
from mcp_india_stack.tools.income_tax_interest import calculate_income_tax_interest
from mcp_india_stack.tools.mobile import validate_mobile_number
from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.ppf_maturity import calculate_ppf_maturity
from mcp_india_stack.tools.presumptive_tax import calculate_presumptive_tax
from mcp_india_stack.tools.professional_tax import calculate_professional_tax
from mcp_india_stack.tools.sip_returns import calculate_sip_returns
from mcp_india_stack.tools.step_up_sip import calculate_step_up_sip
from mcp_india_stack.tools.tds import calculate_tds


class TestPANValidator:
    def test_valid_individual_pan(self) -> None:
        r = validate_pan("ABCPD1234F")
        assert r["valid"] is True
        assert r["entity_type"] == "Individual"

    def test_valid_company_pan_entity_type(self) -> None:
        r = validate_pan("AABCS1429B")
        assert r["valid"] is True
        assert r["entity_type"] in ("Firm", "Company", "AOP", "BOI")

    def test_invalid_pan_format(self) -> None:
        r = validate_pan("AB12C3456D")
        assert r["valid"] is False
        assert r.get("errors") or r.get("error")

    def test_lowercase_normalised(self) -> None:
        r = validate_pan("abcde1234f")
        assert r["valid"] is True


class TestAadhaarValidator:
    def test_valid_aadhaar_masked(self) -> None:
        r = validate_aadhaar("234123412346")
        assert r["valid"] is True
        assert "2346" in str(r.get("masked", ""))
        assert "234123412346" not in json.dumps(r)

    def test_security_full_number_never_exposed(self) -> None:
        # SECURITY: full Aadhaar number must never leak into response
        r = validate_aadhaar("499118665246")
        assert "499118665246" not in json.dumps(r)

    def test_invalid_checksum_aadhaar(self) -> None:
        r = validate_aadhaar("234123412345")
        assert r["valid"] is False


class TestMobileValidator:
    def test_valid_plain_10_digits(self) -> None:
        r = validate_mobile_number("9212102919")
        assert r["valid"] is True, f"9212102919 should be valid, got: {r}"

    def test_valid_with_country_code(self) -> None:
        r = validate_mobile_number("+91 98765 43210")
        assert r["valid"] is True

    def test_valid_91_prefix(self) -> None:
        r = validate_mobile_number("919876543210")
        assert r["valid"] is True

    def test_valid_0_prefix(self) -> None:
        r = validate_mobile_number("09876543210")
        assert r["valid"] is True

    def test_invalid_landline(self) -> None:
        r = validate_mobile_number("01141234567")
        assert r["valid"] is False

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
    def test_all_formats_of_same_number(self, mobile: str) -> None:
        r = validate_mobile_number(mobile)
        assert r["valid"] is True, f"Expected valid for '{mobile}', got: {r}"


class TestIncomeTax:
    def test_new_regime_12L_zero_tax_via_87A(self) -> None:
        r = calculate_income_tax(gross_income=12_00_000, regime="new")
        result = r.get("new_regime") or r.get("tax_new") or r
        total = result.get("total_tax", 0)
        assert total == pytest.approx(0, abs=500)

    def test_new_regime_18L(self) -> None:
        r = calculate_income_tax(gross_income=18_00_000, regime="new")
        result = r.get("new_regime") or r.get("tax_new") or r
        total = result.get("total_tax", 0)
        assert 1_49_000 <= total <= 1_53_000

    def test_old_regime_15L_with_deductions(self) -> None:
        r = calculate_income_tax(
            gross_income=15_00_000,
            regime="old",
            deduction_80c=1_50_000,
            deduction_80d_self=25_000,
            deduction_24b=2_00_000,
        )
        result = r.get("old_regime") or r.get("tax_old") or r
        total = result.get("total_tax", 0)
        assert 1_38_000 <= total <= 1_43_000

    def test_senior_citizen_80D_50K_cap(self) -> None:
        r = calculate_income_tax(
            gross_income=8_00_000, regime="old", age=65, deduction_80d_self=50_000
        )
        result = r.get("old_regime") or r.get("tax_old") or r
        total = result.get("total_tax", 0)
        if "deductions" in result:
            assert result["deductions"]["section_80d"] == 50_000
        assert 50_000 <= total <= 55_000  # 54,600 actual: 7L taxable × old slabs + 4% cess

    def test_both_regime_comparison(self) -> None:
        r = calculate_income_tax(
            gross_income=15_00_000,
            regime="both",
            deduction_80c=1_50_000,
            deduction_80d_self=25_000,
            deduction_24b=2_00_000,
        )
        assert "recommendation" in r or "better_regime" in r


class TestTDS:
    def test_194C_individual_with_pan(self) -> None:
        r = calculate_tds(section="194C_individual", payment_amount=50_000, pan_available=True)
        assert r.get("tds_amount") == pytest.approx(500, abs=1)
        assert r.get("net_payment") == pytest.approx(49_500, abs=1)

    def test_194C_aggregate_threshold(self) -> None:
        r = calculate_tds(
            section="194C",
            payment_amount=25_000,
            pan_available=True,
            payee_type="company",
            aggregate_payments_ytd=85_000,
        )
        assert r.get("tds_amount") == pytest.approx(500, abs=1)

    def test_194A_senior_citizen_bank_interest(self) -> None:
        r = calculate_tds(
            section="194A_bank", payment_amount=60_000, pan_available=True, is_senior_citizen=True
        )
        assert r.get("tds_amount") == pytest.approx(6_000, abs=1)

    def test_194J_no_pan_20_pct(self) -> None:
        r = calculate_tds(
            section="194J",
            payment_amount=1_00_000,
            pan_available=False,
            payee_type="individual_huf",
        )
        assert r.get("tds_amount") == pytest.approx(20_000, abs=1)

    def test_194S_crypto(self) -> None:
        r = calculate_tds(section="194S", payment_amount=2_00_000, pan_available=True)
        assert r.get("tds_amount") == pytest.approx(2_000, abs=1)


class TestGST:
    def test_intra_state_18pct_split(self) -> None:
        r = calculate_gst(amount=10_000, gst_rate=18, transaction_type="intra_state")
        assert r.get("cgst") == pytest.approx(900, abs=1)
        assert r.get("sgst") == pytest.approx(900, abs=1)
        assert r.get("igst") == pytest.approx(0, abs=1)
        assert r.get("total_with_gst") == pytest.approx(11_800, abs=1)

    def test_inter_state_18pct_igst_only(self) -> None:
        r = calculate_gst(amount=50_000, gst_rate=18, transaction_type="inter_state")
        assert r.get("igst") == pytest.approx(9_000, abs=1)
        assert r.get("cgst") == pytest.approx(0, abs=1)
        assert r.get("sgst") == pytest.approx(0, abs=1)

    def test_reverse_gst_calculation(self) -> None:
        r = calculate_gst(amount=11_800, gst_rate=18, amount_includes_gst=True)
        assert r.get("base_amount") == pytest.approx(10_000, abs=1)
        assert r.get("total_gst") == pytest.approx(1_800, abs=1)

    def test_hsn_8517_rate_18pct(self) -> None:
        r = calculate_gst(amount=75_000, hsn_code="8517", transaction_type="inter_state")
        assert r.get("igst") == pytest.approx(13_500, abs=50)
        assert r.get("rate_source") in ("hsn_lookup", "hsn")


class TestGSTLateFee:
    def test_gstr3b_30_days_late(self) -> None:
        r = calculate_gst_late_fee(
            return_type="GSTR3B",
            days_delayed=30,
            annual_turnover=80_00_000,
            has_nil_liability=False,
        )
        assert r.get("total_late_fee") == pytest.approx(1_500, abs=1)
        assert r.get("cgst_fee") == pytest.approx(750, abs=1)
        assert r.get("sgst_fee") == pytest.approx(750, abs=1)

    def test_gstr9_cap_enforced(self) -> None:
        r = calculate_gst_late_fee(return_type="GSTR9", days_delayed=400, annual_turnover=20_00_000)
        assert r.get("total_late_fee") == pytest.approx(5000, abs=1), (
            f"GSTR9 cap not enforced. Got ₹{r.get('total_late_fee')} instead of ₹500"
        )

    def test_nil_return_daily_fee_is_20(self) -> None:
        r = calculate_gst_late_fee(
            return_type="GSTR3B", days_delayed=10, annual_turnover=50_00_000, has_nil_liability=True
        )
        assert r.get("daily_fee") == 20
        assert r.get("total_late_fee") == pytest.approx(200, abs=1)


class TestCapitalGains:
    def test_equity_ltcg_with_1L_exemption(self) -> None:
        r = calculate_capital_gains(
            purchase_price=600,
            sale_price=1000,
            quantity=500,
            asset_type="equity",
            holding_period_days=396,
        )
        assert r.get("is_long_term") is True
        assert r.get("tax_amount") == pytest.approx(12_500, abs=100)

    def test_equity_stcg_8_months(self) -> None:
        r = calculate_capital_gains(
            purchase_price=60_000,
            sale_price=80_000,
            asset_type="equity_mf",
            holding_period_days=243,
        )
        assert r.get("is_long_term") is False
        assert r.get("gain_type", "").upper() == "STCG"
        assert r.get("tax_amount") == pytest.approx(4_000, abs=100)

    def test_real_estate_ltcg_with_indexation(self) -> None:
        r = calculate_capital_gains(
            purchase_price=30_00_000,
            sale_price=80_00_000,
            asset_type="real_estate",
            holding_period_days=9 * 365,
            inflation_index_purchase=240,
            inflation_index_sale=348,
            expenses_on_sale=2_00_000,
        )
        indexed_cost = 30_00_000 * (348 / 240)
        expected_ltcg = 80_00_000 - indexed_cost - 2_00_000
        assert r.get("is_long_term") is True
        actual_gain = r.get("taxable_gain") or r.get("capital_gain") or r.get("net_gain", 0)
        assert actual_gain == pytest.approx(expected_ltcg, rel=0.02)

    def test_real_estate_18_months_is_stcg(self) -> None:
        r = calculate_capital_gains(
            purchase_price=20_00_000,
            sale_price=28_00_000,
            asset_type="real_estate",
            holding_period_days=548,
        )
        assert r.get("is_long_term") is False, (
            "18-month real estate must be STCG — holding period threshold is 24 months (730 days)"
        )
        assert r.get("gain_type", "").upper() == "STCG"

    def test_gold_2_years_is_stcg(self) -> None:
        r = calculate_capital_gains(
            purchase_price=3_00_000, sale_price=5_00_000, asset_type="gold", holding_period_days=730
        )
        assert r.get("is_long_term") is False, (
            "Gold held 24 months must be STCG — threshold is 36 months (1095 days)"
        )

    def test_crypto_flat_30pct(self) -> None:
        r = calculate_capital_gains(
            purchase_price=1_00_000,
            sale_price=4_00_000,
            asset_type="crypto",
            holding_period_days=730,
        )
        assert r.get("tax_amount") == pytest.approx(90_000, abs=500)
        assert r.get("gain_type", "").upper() != "LTCG"


class TestEPFESIC:
    def test_below_esic_ceiling_epf_correct(self) -> None:
        r = calculate_epf_esic(basic_wages=18_000, gross_wages=25_000)
        epf = r.get("epf", r)
        assert epf.get("employee_epf_deduction") == pytest.approx(1_800, abs=1)
        esic = r.get("esic", {})
        assert esic.get("applicable") is False

    def test_above_ceiling_statutory_epf(self) -> None:
        r = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000, voluntary_pf_on_actual=False)
        epf = r.get("epf", r)
        actual = epf.get("employee_epf_deduction")
        assert actual == pytest.approx(1_800, abs=1), (
            f"Statutory EPF should be ₹1,800 (ceiling cap), got ₹{actual}"
        )

    def test_voluntary_pf_uses_full_basic(self) -> None:
        r = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000, voluntary_pf_on_actual=True)
        epf = r.get("epf", r)
        assert epf.get("employee_epf_deduction") == pytest.approx(3_600, abs=1)


class TestGratuity:
    def test_6yr_8mo_rounds_to_7(self) -> None:
        r = calculate_gratuity(last_drawn_salary=45_000, years_of_service=6 + 8 / 12)
        assert r.get("completed_years_for_calculation") == 7
        assert r.get("gratuity_amount") == pytest.approx(45_000 * 15 * 7 / 26, abs=10)
        assert r.get("taxable_gratuity", 0) == 0

    def test_boundary_4yr_6mo_rounds_to_5(self) -> None:
        r = calculate_gratuity(last_drawn_salary=40_000, years_of_service=4.5)
        assert r.get("completed_years_for_calculation") == 5
        assert r.get("minimum_service_met") is True
        assert r.get("gratuity_amount") == pytest.approx(40_000 * 15 * 5 / 26, abs=10)


class TestHRA:
    def test_mumbai_metro_50pct(self) -> None:
        r = calculate_hra_exemption(
            basic_salary=6_00_000, hra_received=3_00_000, rent_paid=3_60_000, city_type="metro"
        )
        assert r.get("exempt_hra") == pytest.approx(3_00_000, abs=1)
        assert r.get("taxable_hra") == pytest.approx(0, abs=1)

    def test_bangalore_non_metro_40pct(self) -> None:
        r = calculate_hra_for_salary_structure(
            monthly_basic=50_000, monthly_hra=25_000, monthly_rent=30_000, city="Bangalore"
        )
        assert r.get("exempt_hra") == pytest.approx(2_40_000, abs=1)
        assert r.get("warnings", []), (
            "Bangalore should generate a non-metro HRA warning for clarity"
        )
        assert r.get("warnings", [])


class TestProfessionalTax:
    def test_maharashtra_25k_annual_2500(self) -> None:
        r = calculate_professional_tax(gross_salary_monthly=25_000, state_code="MH")
        assert r.get("annual_pt") == pytest.approx(2_500, abs=1), (
            f"Maharashtra PT for ₹25K/month should be ₹2,500/year, got ₹{r.get('annual_pt')}"
        )
        assert r.get("monthly_pt") == pytest.approx(200, abs=1)
        assert r.get("february_pt") == pytest.approx(300, abs=1)


class TestPresumptiveTax:
    def test_44ADA_60L_new_regime_all_slabs(self) -> None:
        r = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=60_00_000, digital_receipt_percent=100, regime="new"
        )
        tax = r.get("tax_after_cess") or r.get("total_tax", 0)
        assert tax >= 4_50_000, "Likely truncated slab calculation (only 3 slabs instead of 7)"
        assert tax <= 5_20_000

    def test_44AD_80L_digital_eligible(self) -> None:
        r = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=80_00_000, digital_receipt_percent=80, regime="new"
        )
        assert not r.get("errors"), (
            f"₹80L should be within 44AD limit. Got errors: {r.get('errors')}"
        )
        assert r.get("presumptive_income", 0) > 0

    def test_44ADA_30L_old_regime_with_80c(self) -> None:
        """Old regime 44ADA — covers lines 57-63 (old regime tax path).

        Gross receipts ₹30L, 44ADA, old regime, 80C=₹1.5L.
        Presumptive income = ₹30L × 50% = ₹15L.
        Taxable = ₹15L - ₹1.5L (80C) - ₹50K (SD) = ₹13L.
        Slab tax = ₹2,02,500. Cess = ₹8,100. Total = ₹2,10,600.
        """
        r = calculate_presumptive_tax(
            scheme="44ADA",
            gross_receipts=30_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=1_50_000,
        )
        assert not r.get("errors"), f"Should be eligible: {r.get('errors')}"
        assert r.get("presumptive_income") == pytest.approx(15_00_000, abs=1)
        tax = r.get("tax_after_cess") or r.get("total_tax_payable", 0)
        assert 2_08_000 <= tax <= 2_13_000, (
            f"Expected ≈₹2,10,600 for 44ADA ₹30L old regime, got ₹{tax:,.0f}"
        )

    def test_44ADA_old_regime_87A_rebate(self) -> None:
        """Old regime 44ADA with 87A rebate — covers lines 64-66 (rebate branch).

        Gross receipts ₹8L, 44ADA, old regime, no deductions.
        Presumptive income = ₹4L. Taxable = ₹3.5L (after ₹50K SD).
        87A rebate applies (taxable ≤ ₹5L) → tax = ₹0.
        """
        r = calculate_presumptive_tax(
            scheme="44ADA",
            gross_receipts=8_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert not r.get("errors"), f"Should be eligible: {r.get('errors')}"
        tax = r.get("tax_after_cess") or r.get("total_tax_payable", 0)
        assert tax == pytest.approx(0, abs=1), (
            f"Old regime 87A rebate should zero the tax for ₹8L 44ADA, got ₹{tax:,.0f}"
        )

    def test_44AD_old_regime_cash_heavy(self) -> None:
        """44AD old regime, cash-heavy receipts — covers 44AD old regime path.

        Gross receipts ₹50L, 44AD, 30% digital, old regime.
        Presumptive rate = 0.06×0.30 + 0.08×0.70 = 7.4%.
        Presumptive income = ₹3.7L. Taxable = ₹3.2L after ₹50K SD.
        87A rebate applies → tax = ₹0.
        """
        r = calculate_presumptive_tax(
            scheme="44AD",
            gross_receipts=50_00_000,
            digital_receipt_percent=30,
            regime="old",
            deductions_80c=0,
        )
        assert not r.get("errors"), f"Should be eligible: {r.get('errors')}"
        assert r.get("presumptive_income") == pytest.approx(50_00_000 * 0.074, rel=0.01)
        tax = r.get("tax_after_cess") or r.get("total_tax_payable", 0)
        assert tax == pytest.approx(0, abs=1), (
            f"87A rebate should apply, expected ₹0 tax, got ₹{tax:,.0f}"
        )


class TestSIPReturns:
    def test_10K_monthly_12pct_15yr(self) -> None:
        r = calculate_sip_returns(
            monthly_investment=10_000, expected_annual_return=12, tenure_years=15
        )
        corpus = r.get("estimated_corpus") or r.get("corpus", 0)
        assert 48_00_000 <= corpus <= 53_00_000, (
            f"SIP ₹10K/12%/15yr corpus should be ≈₹50.4L, got ₹{corpus:,.0f}"
        )
        assert r.get("total_invested", 0) == pytest.approx(18_00_000, abs=1_000)


class TestStepUpSIP:
    def test_5K_10pct_stepup_12pct_20yr(self) -> None:
        r = calculate_step_up_sip(
            initial_monthly_investment=5_000,
            annual_step_up_percent=10,
            expected_annual_return=12,
            tenure_years=20,
        )
        corpus = r.get("estimated_corpus", 0)
        assert 90_00_000 <= corpus <= 1_10_00_000, (
            f"Step-up SIP corpus should be ≈₹99-100L (simple rate), got ₹{corpus:,.0f}"
        )
        assert corpus > r.get("flat_sip_corpus", 0)


class TestFDMaturity:
    def test_senior_citizen_fd_quarterly_2yr(self) -> None:
        r = calculate_fd_maturity(
            principal=5_00_000, annual_rate=7.25, tenure_years=2, compounding_frequency=4
        )
        assert 5_74_000 <= r.get("maturity_amount", 0) <= 5_80_000


class TestPPFMaturity:
    def test_1_5L_yearly_71pct_15yr(self) -> None:
        r = calculate_ppf_maturity(annual_investment=1_50_000, annual_rate=7.1, tenure_years=15)
        assert 38_00_000 <= r.get("maturity_amount", 0) <= 43_00_000
        assert r.get("total_invested", 0) == pytest.approx(22_50_000, abs=1_000)


class TestEMI:
    def test_home_loan_50L_8_5pct_20yr(self) -> None:
        r = calculate_emi(principal=50_00_000, annual_interest_rate=8.5, tenure_months=240)
        assert not r.get("errors")
        emi = r.get("monthly_emi") or r.get("emi", 0)
        assert 42_500 <= emi <= 44_500

    def test_zero_interest_emi(self) -> None:
        r = calculate_emi(principal=60_000, annual_interest_rate=0, tenure_months=12)
        assert not r.get("errors")
        emi = r.get("monthly_emi") or r.get("emi", 0)
        assert emi == pytest.approx(5_000, abs=1)
        assert r.get("total_interest", -1) == pytest.approx(0, abs=1)

    def test_negative_principal_returns_error(self) -> None:
        r = calculate_emi(principal=-5_00_000, annual_interest_rate=8.5, tenure_months=240)
        assert r.get("errors")
        assert not r.get("monthly_emi") and not r.get("emi")

    def test_tenure_overflow_returns_error(self) -> None:
        r = calculate_emi(principal=5_00_000, annual_interest_rate=14, tenure_months=400)
        assert r.get("errors")
        assert not r.get("monthly_emi") and not r.get("emi")


class TestAdvanceTax:
    def test_installment_amounts_are_incremental(self) -> None:
        r = calculate_advance_tax(tax_liability=2_40_000)
        installments = r.get("installments", [])
        assert len(installments) == 4
        q1, q2, q3, q4 = installments
        assert q1.get("installment_amount") == pytest.approx(36_000, abs=1)
        assert q2.get("installment_amount") == pytest.approx(72_000, abs=1)
        assert q3.get("installment_amount") == pytest.approx(72_000, abs=1)
        assert q4.get("installment_amount") == pytest.approx(60_000, abs=1)
        assert sum([q.get("installment_amount") for q in installments]) == 2_40_000

    def test_cumulative_amounts_correct(self) -> None:
        r = calculate_advance_tax(tax_liability=2_40_000)
        installments = r.get("installments", [])
        assert installments[1].get("cumulative_amount") == pytest.approx(1_08_000, abs=1)


class TestIncomeTaxInterest:
    def test_234B_no_advance_tax(self) -> None:
        r = calculate_income_tax_interest(total_tax_liability=1_20_000, advance_tax_paid=None)
        s234b = r.get("section_234b", {})
        interest = s234b.get("interest_amount")
        assert interest == pytest.approx(3_600, abs=100)

    def test_234C_q1_missed_interest_charged(self) -> None:
        r = calculate_income_tax_interest(
            total_tax_liability=1_00_000,
            advance_tax_paid={"q1": 0, "q2": 45_000, "q3": 30_000, "q4": 25_000},
            tds_deducted=0,
        )
        s234c = r.get("section_234c", {})
        assert s234c.get("total_234c_interest", 0) == pytest.approx(450, abs=50)


class TestAllRegressions:
    def test_R1_mobile_9212102919_is_valid(self) -> None:
        assert validate_mobile_number("9212102919")["valid"] is True

    def test_R1_aadhaar_no_leak(self) -> None:
        assert "499118665246" not in json.dumps(validate_aadhaar("499118665246"))

    def test_R1_hsn_8517_is_18pct(self) -> None:
        assert calculate_gst(amount=10_000, hsn_code="8517", transaction_type="inter_state").get(
            "igst"
        ) == pytest.approx(1_800, abs=50)

    def test_R1_professional_tax_maharashtra_annual(self) -> None:
        assert calculate_professional_tax(25_000, "MH").get("annual_pt") == pytest.approx(
            2_500, abs=1
        )

    def test_R1_real_estate_18mo_is_stcg(self) -> None:
        assert (
            calculate_capital_gains(
                20_00_000, 28_00_000, asset_type="real_estate", holding_period_days=548
            ).get("is_long_term")
            is False
        )

    def test_R2_44AD_80L_within_3cr_limit(self) -> None:
        assert not calculate_presumptive_tax(
            scheme="44AD", gross_receipts=80_00_000, digital_receipt_percent=80, regime="new"
        ).get("errors")

    def test_R2_epf_ceiling_cap(self) -> None:
        epf = calculate_epf_esic(30_000, 50_000, voluntary_pf_on_actual=False).get("epf", {})
        assert epf.get("employee_epf_deduction") == pytest.approx(1_800, abs=1)

    def test_R2_bangalore_hra_non_metro(self) -> None:
        r = calculate_hra_for_salary_structure(
            monthly_basic=50_000, monthly_hra=25_000, monthly_rent=30_000, city="Bangalore"
        )
        assert r.get("exempt_hra") == pytest.approx(2_40_000, abs=1)

    def test_R2_presumptive_full_slabs(self) -> None:
        r = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=60_00_000, digital_receipt_percent=100, regime="new"
        )
        tax = r.get("tax_after_cess") or r.get("total_tax", 0)
        assert tax >= 4_50_000

    def test_R2_gstr9_cap(self) -> None:
        assert calculate_gst_late_fee(
            return_type="GSTR9", days_delayed=400, annual_turnover=20_00_000
        ).get("total_late_fee") == pytest.approx(5000, abs=1)

    def test_R2_advance_tax_incremental(self) -> None:
        installments = calculate_advance_tax(tax_liability=2_40_000).get("installments", [])
        assert installments[0].get("installment_amount") == pytest.approx(36_000, abs=1)

    def test_R2_234C_cumulative(self) -> None:
        r = calculate_income_tax_interest(
            total_tax_liability=1_00_000,
            advance_tax_paid={"q1": 0, "q2": 45_000, "q3": 30_000, "q4": 25_000},
            tds_deducted=0,
        )
        assert r.get("section_234c", {}).get("total_234c_interest", 0) == pytest.approx(450, abs=50)
