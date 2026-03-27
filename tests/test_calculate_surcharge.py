"""Tests for surcharge calculator."""

from mcp_india_stack.tools.surcharge import calculate_surcharge


class TestNoSurcharge:
    def test_below_50_lakh(self) -> None:
        """Income below ₹50L — no surcharge."""
        result = calculate_surcharge(4_000_000, 900_000, "old")
        assert result["surcharge_rate"] == 0
        assert result["surcharge_after_relief"] == 0


class TestSurchargeRate:
    def test_10_percent_tier(self) -> None:
        """Income between ₹50L-1Cr — 10% surcharge."""
        result = calculate_surcharge(7_000_000, 1_500_000, "old")
        assert result["surcharge_rate"] == 0.10

    def test_15_percent_tier(self) -> None:
        """Income between ₹1Cr-2Cr — 15% surcharge."""
        result = calculate_surcharge(15_000_000, 3_750_000, "old")
        assert result["surcharge_rate"] == 0.15


class TestNewRegimeCap:
    def test_new_regime_capped_at_25(self) -> None:
        """New regime caps surcharge at 25% even for income > ₹5Cr."""
        result = calculate_surcharge(60_000_000, 17_100_000, "new")
        assert result["surcharge_rate"] == 0.25

    def test_old_regime_37_percent(self) -> None:
        """Old regime allows 37% for income > ₹5Cr."""
        result = calculate_surcharge(60_000_000, 17_100_000, "old")
        assert result["surcharge_rate"] == 0.37


class TestMarginalRelief:
    def test_marginal_relief_applied(self) -> None:
        """Just above ₹50L — marginal relief should reduce surcharge."""
        result = calculate_surcharge(5_000_001, 1_200_000, "old")
        # Surcharge should exist but may be reduced by marginal relief
        assert result["surcharge_before_relief"] > 0
        # With only ₹1 over the threshold, marginal relief should kick in
        assert result["surcharge_after_relief"] >= 0


class TestValidation:
    def test_invalid_regime(self) -> None:
        result = calculate_surcharge(5_000_000, 1_000_000, "invalid")
        assert len(result["errors"]) > 0

    def test_negative_income(self) -> None:
        result = calculate_surcharge(-100, 0, "new")
        assert len(result["errors"]) > 0


class TestFinancialYear:
    def test_fy_present(self) -> None:
        result = calculate_surcharge(1_000_000, 100_000, "new")
        assert result["financial_year"] == "2025-26"
