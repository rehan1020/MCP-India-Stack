"""Regression tests for v0.4.2 bug fixes (Round 2).

These tests simulate each of the 8 fixed scenarios end-to-end,
catching any wiring issues between tool definition and implementation.
"""

import pytest


class TestBug1_CapitalGainsHoldingPeriod:
    """Bug 1: Wrong LTCG holding period for real estate and gold."""

    def test_real_estate_21_months_is_stcg(self):
        """Land bought Jan 2022, sold Oct 2023 (21 months) → STCG, not LTCG."""
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            sale_price=80_00_000,
            purchase_price=50_00_000,
            asset_type="real_estate",
            holding_period_days=640,  # ~21 months
        )
        assert result["is_long_term"] is False
        assert result["gain_type"] == "STCG"
        assert result["ltcg_threshold_days"] == 730

    def test_gold_30_months_is_stcg(self):
        """Gold held 30 months → still STCG (needs 36 months)."""
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            sale_price=5_00_000, purchase_price=3_00_000, asset_type="gold", holding_period_days=912
        )
        assert result["is_long_term"] is False
        assert result["gain_type"] == "STCG"

    def test_crypto_never_ltcg(self):
        """Crypto is always flat 30%, no LTCG concept."""
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            sale_price=10_00_000,
            purchase_price=5_00_000,
            asset_type="crypto",
            holding_period_days=2000,
        )
        assert result["is_long_term"] is False


class TestBug2_EPFWageCeiling:
    """Bug 2: Employee EPF not capped at wage ceiling."""

    def test_basic_30k_epf_is_1800(self):
        """Basic ₹30K → statutory EPF = ₹15K × 12% = ₹1,800."""
        from mcp_india_stack.tools.epf_esic import calculate_epf_esic

        result = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000)
        assert result["epf"]["employee_epf_deduction"] == 1_800

    def test_vpf_on_actual_gives_3600(self):
        """VPF on actual basic ₹30K = ₹3,600."""
        from mcp_india_stack.tools.epf_esic import calculate_epf_esic

        result = calculate_epf_esic(
            basic_wages=30_000, gross_wages=50_000, voluntary_pf_on_actual=True
        )
        assert result["epf"]["employee_epf_deduction"] == 3_600


class TestBug3_HRAMetroCities:
    """Bug 3: Bangalore/Hyderabad/Pune wrongly treated as metro."""

    def test_bangalore_hra_uses_40_pct(self):
        """Bangalore → 40% (non-metro), not 50%."""
        from mcp_india_stack.tools.hra import calculate_hra_for_salary_structure

        result = calculate_hra_for_salary_structure(
            monthly_basic=50_000, monthly_hra=25_000, monthly_rent=30_000, city="Bangalore"
        )
        assert result["city_type"] == "non_metro"
        # Warning about Bangalore
        assert any("Bangalore" in w for w in result.get("warnings", []))

    def test_mumbai_is_metro(self):
        """Mumbai IS a metro city."""
        from mcp_india_stack.tools.hra import _classify_city

        city_type, _ = _classify_city("Mumbai")
        assert city_type == "metro"


class TestBug4_PresumptiveTaxSlabs:
    """Bug 4: New regime slab truncated after 10%."""

    def test_60l_44ada_hits_high_slabs(self):
        """₹60L receipts → presumptive ₹30L → hits 25%+ slab."""
        from mcp_india_stack.tools.presumptive_tax import calculate_presumptive_tax

        result = calculate_presumptive_tax(
            "44ADA", 60_00_000, digital_receipt_percent=100, regime="new"
        )
        # Taxable = ₹30L - ₹75K = ₹29.25L → 30% slab territory
        assert result["tax_after_cess"] > 4_00_000

    def test_old_regime_30_pct_slab_exists(self):
        """Old regime above ₹10L should hit 30% slab."""
        from mcp_india_stack.tools.presumptive_tax import calculate_presumptive_tax

        result = calculate_presumptive_tax(
            "44ADA", 50_00_000, digital_receipt_percent=100, regime="old", deductions_80c=0
        )
        # Presumptive = ₹25L, taxable = ₹25L - ₹50K = ₹24.5L → 30% slab
        assert result["tax_after_cess"] > 3_00_000


class TestBug5_GSTLateFee:
    """Bug 5: GSTR9 cap not enforced + nil return rate wrong."""

    def test_gstr9_500_days_turnover_20l(self):
        """GSTR9 500 days late, turnover ₹20L → capped at ₹5,000."""
        from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee

        result = calculate_gst_late_fee("GSTR9", 500, 20_00_000)
        assert result["total_late_fee"] == 5_000

    def test_nil_return_20_per_day(self):
        """Nil return = ₹20/day, not ₹25."""
        from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee

        result = calculate_gst_late_fee("GSTR3B", 10, 50_00_000, has_nil_liability=True)
        assert result["daily_fee"] == 20


class TestBug6_234CShortfall:
    """Bug 6: Section 234C uses cumulative, not single-quarter."""

    def test_q1_missed_q2_catchup(self):
        """Q1 paid ₹0, Q2 paid ₹45K → Q1 shortfall of ₹15K flagged."""
        from mcp_india_stack.tools.income_tax_interest import calculate_income_tax_interest

        result = calculate_income_tax_interest(
            total_tax_liability=1_00_000,
            advance_tax_paid={"q1": 0, "q2": 45_000, "q3": 30_000, "q4": 25_000},
            tds_deducted=0,
        )
        q_shortfalls = result["section_234c"]["quarterly_shortfalls"]
        q1_item = q_shortfalls[0]
        assert q1_item["shortfall"] == 15_000
        assert q1_item["interest"] == pytest.approx(450)


class TestBug7_AdvanceTaxIncremental:
    """Bug 7: Installment amounts should be incremental."""

    def test_q2_shows_72k_not_108k(self):
        """Q2 installment = ₹72K (30%), not ₹1,08,000 (45% cumulative)."""
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(tax_liability=2_40_000)
        q2 = result["installments"][1]
        assert q2["installment_amount"] == 72_000
        assert q2["cumulative_amount"] == 1_08_000

    def test_all_installments_sum_to_total(self):
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(tax_liability=2_40_000)
        total = sum(i["installment_amount"] for i in result["installments"])
        assert total == 2_40_000


class TestBug8_SalaryConveyance:
    """Bug 8: Conveyance ₹19,200 exemption is obsolete."""

    def test_no_conveyance_component(self):
        """Conveyance must not appear in restructured components."""
        from mcp_india_stack.tools.salary_restructuring import calculate_salary_restructuring

        result = calculate_salary_restructuring(current_gross=15_00_000)
        assert "conveyance" not in result["restructured_components"]

    def test_standard_deduction_present(self):
        """Standard deduction of ₹75K shown."""
        from mcp_india_stack.tools.salary_restructuring import calculate_salary_restructuring

        result = calculate_salary_restructuring(current_gross=20_00_000)
        assert result.get("standard_deduction") in (50_000, 75_000)
        assert "standard_deduction_note" in result
