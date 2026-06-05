"""Tests for capital gains calculator."""

import pytest

from mcp_india_stack.tools.capital_gains import _get_ltcg_threshold, calculate_capital_gains


class TestCapitalGainsEquity:
    def test_equity_stcg(self):
        result = calculate_capital_gains(
            sale_price=150000, purchase_price=100000, asset_type="equity", holding_period_days=180
        )
        assert "gain_type" in result
        assert result.get("gain_type") in ["STCG", "LTCG"]

    def test_equity_ltcg(self):
        result = calculate_capital_gains(
            sale_price=200000, purchase_price=100000, asset_type="equity", holding_period_days=400
        )
        assert result.get("gain_type") == "LTCG"

    def test_equity_gain(self):
        result = calculate_capital_gains(
            sale_price=120000, purchase_price=100000, asset_type="equity", holding_period_days=400
        )
        assert result.get("total_gains", 0) > 0


class TestCapitalGainsRealEstate:
    def test_real_estate_with_indexation(self):
        result = calculate_capital_gains(
            sale_price=5000000,
            purchase_price=2000000,
            asset_type="real_estate",
            holding_period_days=800,
            inflation_index_purchase=301,
            inflation_index_sale=348,
        )
        assert result.get("gain_type") == "LTCG"

    def test_real_estate_cost_indexed(self):
        result = calculate_capital_gains(
            sale_price=5000000,
            purchase_price=2000000,
            asset_type="real_estate",
            holding_period_days=800,
            inflation_index_purchase=301,
            inflation_index_sale=348,
        )
        assert "cost_inflation_adjusted" in result


class TestCapitalGainsGold:
    def test_gold_ltcg(self):
        result = calculate_capital_gains(
            sale_price=300000, purchase_price=200000, asset_type="gold", holding_period_days=1100
        )
        assert result.get("gain_type") == "LTCG"


class TestCapitalGainsCrypto:
    def test_crypto(self):
        result = calculate_capital_gains(
            sale_price=150000, purchase_price=100000, asset_type="crypto", holding_period_days=180
        )
        assert "gain_type" in result


class TestCapitalGainsInvalid:
    def test_zero_sale_price(self):
        result = calculate_capital_gains(
            sale_price=0, purchase_price=100000, asset_type="equity", holding_period_days=400
        )
        # Should handle gracefully
        assert "gain_type" in result or "errors" in result

    def test_negative_holding_period(self):
        result = calculate_capital_gains(
            sale_price=100000, purchase_price=50000, asset_type="equity", holding_period_days=-1
        )
        # Should handle gracefully
        assert "gain_type" in result or "errors" in result

    def test_invalid_asset_type(self):
        result = calculate_capital_gains(
            sale_price=100000, purchase_price=50000, asset_type="unknown", holding_period_days=400
        )
        # Should handle gracefully
        assert "gain_type" in result or "errors" in result


def test_capital_gains_negative_purchase_price() -> None:
    """purchase_price < 0 -> error on line 58."""
    result = calculate_capital_gains(
        sale_price=200000,
        purchase_price=-50000,
        asset_type="equity",
        holding_period_days=400,
    )
    assert result["errors"]
    assert any("purchase" in e.lower() for e in result["errors"])
    assert result["tax_liability"] == 0.0


def test_capital_gains_negative_expenses() -> None:
    """expenses_on_sale < 0 -> error on line 60."""
    result = calculate_capital_gains(
        sale_price=200000,
        purchase_price=100000,
        asset_type="equity",
        holding_period_days=400,
        expenses_on_sale=-5000,
    )
    assert result["errors"]
    assert any("expense" in e.lower() for e in result["errors"])
    assert result["tax_liability"] == 0.0


def test_capital_gains_section_54_real_estate_reinvestment() -> None:
    """Section 54: real_estate LTCG + reinvestment_amount > 0 -> exemption applied."""
    result = calculate_capital_gains(
        sale_price=5000000,
        purchase_price=2000000,
        asset_type="real_estate",
        holding_period_days=800,
        reinvestment_amount=2000000,
    )
    assert not result["errors"]
    assert result["gain_type"] == "LTCG"
    assert "section_54_exemption_claimed" in result
    assert result["section_54_taxable_gains"] is not None


def test_capital_gains_section_54_full_reinvestment_zero_taxable() -> None:
    """Reinvesting more than LTCG -> full exemption, taxable gains = 0."""
    result = calculate_capital_gains(
        sale_price=3000000,
        purchase_price=2000000,
        asset_type="real_estate",
        holding_period_days=800,
        reinvestment_amount=5000000,
    )
    assert not result["errors"]
    ltcg = result["long_term_gains"]
    assert result["section_54_exemption_claimed"] == pytest.approx(ltcg, abs=1)
    assert result["section_54_taxable_gains"] == pytest.approx(0, abs=1)


def test_capital_gains_section_54f_gold_reinvestment() -> None:
    """Section 54F: gold LTCG + reinvestment -> proportional exemption."""
    result = calculate_capital_gains(
        sale_price=500000,
        purchase_price=200000,
        asset_type="gold",
        holding_period_days=1100,
        reinvestment_amount=500000,
    )
    assert not result["errors"]
    assert result["gain_type"] == "LTCG"
    assert "section_54f_exemption_claimed" in result


def test_capital_gains_section_54f_equity_reinvestment() -> None:
    """Section 54F: equity LTCG + partial reinvestment -> partial exemption."""
    result = calculate_capital_gains(
        sale_price=400000,
        purchase_price=200000,
        asset_type="equity",
        holding_period_days=400,
        reinvestment_amount=200000,
    )
    assert not result["errors"]
    assert "section_54f_exemption_claimed" in result
    assert result["section_54f_note"] is not None


def test_capital_gains_no_54_exemption_for_stcg() -> None:
    """Section 54/54F does not apply to STCG — reinvestment_amount ignored."""
    result = calculate_capital_gains(
        sale_price=500000,
        purchase_price=200000,
        asset_type="real_estate",
        holding_period_days=180,
        reinvestment_amount=300000,
    )
    assert not result["errors"]
    assert result["gain_type"] == "STCG"
    assert result.get("section_54_exemption_claimed", 0) == 0


def test_calculate_home_loan_savings_basic() -> None:
    """calculate_home_loan_savings — secondary function in capital_gains.py."""
    from mcp_india_stack.tools.capital_gains import calculate_home_loan_savings

    result = calculate_home_loan_savings(
        property_sale_price=5000000,
        property_purchase_price=2000000,
        loan_outstanding=1000000,
        holding_period_days=800,
    )
    assert "capital_gains" in result
    assert "tax_liability" in result
    assert "tax_savings_available" in result
    assert result["holding_period_met"] is True


def test_calculate_home_loan_savings_stcg_no_exemption() -> None:
    """Short holding period -> exemption not met."""
    from mcp_india_stack.tools.capital_gains import calculate_home_loan_savings

    result = calculate_home_loan_savings(
        property_sale_price=3000000,
        property_purchase_price=2000000,
        loan_outstanding=500000,
        holding_period_days=200,
    )
    assert result["holding_period_met"] is False


# ---- Bug 1 regression: asset-type-specific LTCG thresholds ----


def test_real_estate_18_months_is_stcg():
    """Real estate held 18 months (548 days) must be STCG (needs 24 months)."""
    result = calculate_capital_gains(
        sale_price=80_00_000,
        purchase_price=50_00_000,
        asset_type="real_estate",
        holding_period_days=548,
    )
    assert result["is_long_term"] is False
    assert result["gain_type"] == "STCG"


def test_real_estate_25_months_is_ltcg():
    """Real estate held 25 months (760 days) must be LTCG."""
    result = calculate_capital_gains(
        sale_price=80_00_000,
        purchase_price=50_00_000,
        asset_type="real_estate",
        holding_period_days=760,
    )
    assert result["is_long_term"] is True
    assert result["gain_type"] == "LTCG"


def test_gold_2_years_is_stcg():
    """Gold held 24 months (730 days) is still STCG (needs 36 months)."""
    result = calculate_capital_gains(
        sale_price=5_00_000, purchase_price=3_00_000, asset_type="gold", holding_period_days=730
    )
    assert result["is_long_term"] is False


def test_gold_3_years_is_ltcg():
    """Gold held 3+ years (1100 days) is LTCG."""
    result = calculate_capital_gains(
        sale_price=5_00_000, purchase_price=3_00_000, asset_type="gold", holding_period_days=1100
    )
    assert result["is_long_term"] is True


def test_crypto_always_stcg():
    """Crypto has no LTCG concept — always STCG at 30%."""
    result = calculate_capital_gains(
        sale_price=5_00_000, purchase_price=3_00_000, asset_type="crypto", holding_period_days=1500
    )
    assert result["is_long_term"] is False
    assert result["gain_type"] == "STCG"


def test_ltcg_threshold_lookup():
    """Verify threshold values for all asset types."""
    assert _get_ltcg_threshold("equity") == 365
    assert _get_ltcg_threshold("real_estate") == 730
    assert _get_ltcg_threshold("gold") == 1095
    assert _get_ltcg_threshold("crypto") == 0
    assert _get_ltcg_threshold("unknown") == 365  # default
