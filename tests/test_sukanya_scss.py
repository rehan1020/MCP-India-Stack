"""Tests for SSY and SCSS calculators."""

import pytest

from mcp_india_stack.tools.sukanya_scss import calculate_sukanya_samriddhi


def test_ssy_max_investment():
    result = calculate_sukanya_samriddhi(
        scheme="ssy", annual_investment=150000, annual_interest_rate=8.2
    )
    assert result.get("maturity_amount") > 4000000


def test_ssy_deposits_15_years_only():
    result = calculate_sukanya_samriddhi(scheme="ssy", annual_investment=100000)
    assert result.get("total_invested") == pytest.approx(1500000, abs=1)


def test_ssy_eee_tax_status():
    result = calculate_sukanya_samriddhi(scheme="ssy", annual_investment=100000)
    assert "EEE" in result.get("tax_status", "")


def test_ssy_maturity_exceeds_invested():
    result = calculate_sukanya_samriddhi(scheme="ssy", annual_investment=50000)
    assert result["maturity_amount"] > result["total_invested"]


def test_ssy_below_minimum_250():
    result = calculate_sukanya_samriddhi(scheme="ssy", annual_investment=200)
    assert "errors" in result


def test_ssy_above_maximum_150000():
    result = calculate_sukanya_samriddhi(scheme="ssy", annual_investment=160000)
    assert "errors" in result


def test_scss_quarterly_interest():
    result = calculate_sukanya_samriddhi(
        scheme="scss", annual_investment=500000, annual_interest_rate=8.2
    )
    expected_total = 500000 * 8.2 / 100 * 5
    assert result.get("total_interest") == pytest.approx(expected_total, rel=0.05)


def test_scss_principal_returned():
    result = calculate_sukanya_samriddhi(
        scheme="scss", annual_investment=500000, annual_interest_rate=8.2
    )
    assert result.get("maturity_amount") > result.get("total_invested")


def test_scss_above_30_lakh():
    result = calculate_sukanya_samriddhi(scheme="scss", annual_investment=31000000)
    assert "errors" in result


def test_invalid_scheme():
    result = calculate_sukanya_samriddhi(scheme="ppf", annual_investment=100000)
    assert "errors" in result
