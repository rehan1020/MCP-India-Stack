"""Tests for Recurring Deposit maturity calculator."""

import pytest

from mcp_india_stack.tools.rd_maturity import calculate_rd_maturity


def test_rd_standard_2yr():
    result = calculate_rd_maturity(
        monthly_installment=10000, annual_interest_rate=6.5, tenure_months=24
    )
    assert result.get("maturity_amount") > result.get("total_invested")
    assert result.get("total_interest") > 0


def test_rd_total_invested_exact():
    result = calculate_rd_maturity(
        monthly_installment=5000, annual_interest_rate=7.0, tenure_months=12
    )
    assert result.get("total_invested") == pytest.approx(60000, abs=1)


def test_rd_longer_tenure_higher_maturity():
    short = calculate_rd_maturity(
        monthly_installment=10000, annual_interest_rate=6.5, tenure_months=12
    )
    long = calculate_rd_maturity(
        monthly_installment=10000, annual_interest_rate=6.5, tenure_months=24
    )
    assert long["maturity_amount"] > short["maturity_amount"]


def test_rd_higher_rate_higher_maturity():
    low = calculate_rd_maturity(
        monthly_installment=5000, annual_interest_rate=5.0, tenure_months=12
    )
    high = calculate_rd_maturity(
        monthly_installment=5000, annual_interest_rate=8.0, tenure_months=12
    )
    assert high["maturity_amount"] > low["maturity_amount"]


def test_rd_maturity_exceeds_invested():
    result = calculate_rd_maturity(
        monthly_installment=10000, annual_interest_rate=7.0, tenure_months=24
    )
    assert result["maturity_amount"] > result["total_invested"]


def test_rd_zero_installment():
    result = calculate_rd_maturity(
        monthly_installment=0, annual_interest_rate=6.5, tenure_months=12
    )
    assert "errors" in result


def test_rd_zero_tenure():
    result = calculate_rd_maturity(
        monthly_installment=5000, annual_interest_rate=6.5, tenure_months=0
    )
    assert "errors" in result


def test_rd_negative_rate():
    result = calculate_rd_maturity(
        monthly_installment=5000, annual_interest_rate=-1.0, tenure_months=12
    )
    assert "errors" not in result or result.get("maturity_amount", 0) > 0
