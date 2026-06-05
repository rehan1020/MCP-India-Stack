"""Tests for step-up SIP calculator."""

import pytest

from mcp_india_stack.tools.step_up_sip import calculate_step_up_sip


def test_step_up_exceeds_flat_sip():
    result = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=10.0,
        expected_annual_return=12.0,
        tenure_years=15,
    )
    assert result.get("estimated_corpus") > result.get("flat_sip_corpus")


def test_step_up_advantage_positive():
    result = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=10.0,
        expected_annual_return=12.0,
        tenure_years=15,
    )
    assert result.get("step_up_advantage") > 0


def test_zero_step_up_equals_flat():
    result = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=0,
        expected_annual_return=12.0,
        tenure_years=15,
    )
    assert result["estimated_corpus"] == pytest.approx(result["flat_sip_corpus"], rel=0.05)


def test_final_sip_amount_computed():
    result = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=10.0,
        expected_annual_return=12.0,
        tenure_years=10,
    )
    expected = 10000 * (1.1**10)
    assert result.get("final_monthly_sip") == pytest.approx(expected, rel=0.02)


def test_higher_step_up_higher_corpus():
    low = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=5.0,
        expected_annual_return=12.0,
        tenure_years=10,
    )
    high = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=15.0,
        expected_annual_return=12.0,
        tenure_years=10,
    )
    assert high["estimated_corpus"] > low["estimated_corpus"]


def test_zero_initial_investment():
    result = calculate_step_up_sip(
        initial_monthly_investment=0,
        annual_step_up_percent=10.0,
        expected_annual_return=12.0,
        tenure_years=10,
    )
    assert "errors" in result


def test_zero_tenure():
    result = calculate_step_up_sip(
        initial_monthly_investment=10000,
        annual_step_up_percent=10.0,
        expected_annual_return=12.0,
        tenure_years=0,
    )
    assert "errors" in result


# --- Bug fix verification tests ---


def test_step_up_sip_basic():
    """₹5,000/month, 10% step-up, 12% return, 20 years → should be ≈₹99.4 lakhs."""
    result = calculate_step_up_sip(5000, 10, 12, 20)
    # Corpus should be between ₹90 Lakhs and ₹1.1 Cr
    assert 90_00_000 < result["estimated_corpus"] < 1_10_00_000
    assert result["total_invested"] == pytest.approx(34_36_500, rel=0.01)


def test_step_up_sip_zero_return():
    """With 0% return and 0% step-up, corpus == total invested."""
    result = calculate_step_up_sip(1000, 0, 0, 5)
    assert result["estimated_corpus"] == pytest.approx(result["total_invested"], rel=0.01)


def test_step_up_better_than_flat():
    result = calculate_step_up_sip(5000, 10, 12, 15)
    assert result["estimated_corpus"] > result["flat_sip_corpus"]
    assert result["step_up_advantage"] > 0
