"""Tests for SIP returns calculator."""

import pytest

from mcp_india_stack.tools.sip_returns import calculate_sip_returns


def test_sip_15yr_12pct_corpus():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=12.0, tenure_years=15
    )
    assert result.get("estimated_corpus") == pytest.approx(5027872, rel=0.05)


def test_sip_total_invested_correct():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=12.0, tenure_years=15
    )
    assert result.get("total_invested") == pytest.approx(1800000, abs=1)


def test_sip_wealth_gained_positive():
    result = calculate_sip_returns(
        monthly_investment=5000, expected_annual_return=10.0, tenure_years=10
    )
    assert result.get("wealth_gained") > 0


def test_sip_real_returns_below_nominal():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=12.0, tenure_years=15, inflation_rate=6.0
    )
    assert result["inflation_adjusted_corpus"] < result["estimated_corpus"]


def test_sip_very_low_return():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=0.1, tenure_years=10
    )
    assert result["estimated_corpus"] > result["total_invested"]


def test_sip_longer_tenure_higher_corpus():
    short = calculate_sip_returns(
        monthly_investment=5000, expected_annual_return=12.0, tenure_years=5
    )
    long = calculate_sip_returns(
        monthly_investment=5000, expected_annual_return=12.0, tenure_years=15
    )
    assert long["estimated_corpus"] > short["estimated_corpus"]


def test_sip_zero_monthly_investment():
    result = calculate_sip_returns(
        monthly_investment=0, expected_annual_return=12.0, tenure_years=10
    )
    assert "errors" in result


def test_sip_zero_tenure():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=12.0, tenure_years=0
    )
    assert "errors" in result


def test_sip_negative_return():
    result = calculate_sip_returns(
        monthly_investment=10000, expected_annual_return=-5.0, tenure_years=10
    )
    assert "errors" not in result or result.get("estimated_corpus", 0) > 0
