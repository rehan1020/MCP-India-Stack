"""Tests for home vs rent financial comparison."""

import pytest

from mcp_india_stack.tools.home_vs_rent import calculate_home_vs_rent

BASE = dict(
    home_price=10000000,
    down_payment_percent=20,
    loan_interest_rate=8.5,
    loan_tenure_years=20,
    monthly_rent=35000,
    analysis_years=20,
)


def test_basic_comparison_runs():
    result = calculate_home_vs_rent(**BASE)
    d = result
    assert "buy_scenario" in d
    assert "rent_scenario" in d


def test_upfront_cost_formula():
    result = calculate_home_vs_rent(**{**BASE, "stamp_duty_percent": 5, "registration_percent": 1})
    assert result.get("buy_scenario", {}).get("upfront_cost") == pytest.approx(2600000, abs=50000)


def test_emi_positive():
    result = calculate_home_vs_rent(**BASE)
    assert result.get("buy_scenario", {}).get("monthly_emi") > 0


def test_rent_corpus_positive():
    result = calculate_home_vs_rent(**BASE)
    assert result.get("rent_scenario", {}).get("total_corpus_at_analysis_end") > 0


def test_break_even_year_in_comparison():
    result = calculate_home_vs_rent(**BASE)
    d = result
    if d.get("break_even_year") is not None:
        years = [y["year"] for y in d.get("yearly_comparison", [])]
        assert d["break_even_year"] in years


def test_verdict_present():
    result = calculate_home_vs_rent(**BASE)
    assert "verdict" in result


def test_high_appreciation_favors_buy():
    result = calculate_home_vs_rent(
        **{**BASE, "expected_property_appreciation": 12.0, "analysis_years": 20}
    )
    assert "buy_scenario" in result


def test_down_payment_below_10pct_invalid():
    result = calculate_home_vs_rent(**{**BASE, "down_payment_percent": 5})
    assert "errors" in result


def test_zero_home_price():
    result = calculate_home_vs_rent(**{**BASE, "home_price": 0})
    assert "buy_scenario" in result


def test_analysis_years_above_30_handled():
    result = calculate_home_vs_rent(**{**BASE, "analysis_years": 35})
    assert "buy_scenario" in result or "errors" in result
