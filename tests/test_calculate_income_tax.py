"""Tests for income tax calculator."""

from mcp_india_stack.tools.income_tax import calculate_income_tax


class TestNewRegimeRebate:
    def test_12_lakh_zero_tax_new_regime(self) -> None:
        """Income of ₹12,00,000 under new regime — 87A rebate makes zero tax."""
        result = calculate_income_tax(1_200_000, regime="new")
        assert result["new_regime"]["total_tax"] == 0

    def test_above_rebate_limit_tax_applies(self) -> None:
        """Gross of ₹12,75,001 — after ₹75K standard deduction, taxable = ₹12,00,001.
        One rupee above 87A rebate limit, full tax applies."""
        result = calculate_income_tax(1_275_001, regime="new")
        assert result["new_regime"]["total_tax"] > 0
        assert result["new_regime"]["rebate_87a"] == 0


class TestSurcharge:
    def test_50_lakh_plus_surcharge(self) -> None:
        """Income above ₹50L triggers surcharge."""
        result = calculate_income_tax(5_000_001, regime="new")
        new = result["new_regime"]
        # Should have surcharge applied
        assert new["total_tax"] > new["tax_after_rebate"]


class TestSeniorCitizen:
    def test_senior_old_regime_higher_exemption(self) -> None:
        """Senior citizen under old regime has ₹3L basic exemption."""
        result = calculate_income_tax(500_000, regime="old", taxpayer_type="senior_citizen")
        old = result["old_regime"]
        # ₹5L income, ₹50K standard deduction = ₹4.5L taxable
        # First ₹3L exempt, then 5% on ₹1.5L = ₹7,500
        # But ₹4.5L <= ₹5L rebate limit, so 87A rebate applies
        assert old["rebate_87a"] > 0


class TestComparison:
    def test_both_regime_returns_recommendation(self) -> None:
        """regime='both' returns recommendation."""
        result = calculate_income_tax(1_500_000, regime="both")
        assert "recommendation" in result
        assert "savings" in result
        assert result["recommendation"] in ("new_regime", "old_regime")


class TestZeroIncome:
    def test_zero_income_zero_tax(self) -> None:
        result = calculate_income_tax(0, regime="new")
        assert result["new_regime"]["total_tax"] == 0


class TestNegativeIncome:
    def test_negative_income_error(self) -> None:
        result = calculate_income_tax(-100000, regime="new")
        assert len(result["errors"]) > 0
        assert "negative" in str(result["errors"]).lower()


class TestFinancialYear:
    def test_fy_2025_26(self) -> None:
        result = calculate_income_tax(1_000_000, regime="new")
        assert result["financial_year"] == "2025-26"
        assert result["assessment_year"] == "2026-27"


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = calculate_income_tax(1_000_000, regime="new")
        assert "disclaimer" in result
        assert "FY2025-26" in result["disclaimer"]
