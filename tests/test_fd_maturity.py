"""Tests for Fixed Deposit maturity calculator."""

import pytest

from mcp_india_stack.tools.fd_maturity import calculate_fd_maturity


def test_fd_quarterly_1yr():
    result = calculate_fd_maturity(
        principal=500000, annual_interest_rate=6.5, tenure_days=365, compounding="quarterly"
    )
    assert result.get("maturity_amount") > 500000
    assert result.get("total_interest") > 0


def test_fd_simple_interest_formula():
    result = calculate_fd_maturity(
        principal=100000, annual_interest_rate=6.0, tenure_days=365, compounding="simple"
    )
    expected_interest = 100000 * 6.0 / 100
    assert result.get("total_interest") == pytest.approx(expected_interest, abs=10)


def test_fd_compound_beats_simple():
    kwargs = dict(principal=100000, annual_interest_rate=6.0, tenure_days=365)
    compound = calculate_fd_maturity(**kwargs, compounding="quarterly")
    simple = calculate_fd_maturity(**kwargs, compounding="simple")
    assert compound["maturity_amount"] > simple["maturity_amount"]


def test_fd_senior_citizen_higher_maturity():
    normal = calculate_fd_maturity(
        principal=100000, annual_interest_rate=6.5, tenure_days=365, is_senior_citizen=False
    )
    senior = calculate_fd_maturity(
        principal=100000,
        annual_interest_rate=6.5,
        tenure_days=365,
        is_senior_citizen=True,
        senior_citizen_bonus=0.5,
    )
    assert senior["maturity_amount"] > normal["maturity_amount"]


def test_fd_tds_above_40k_threshold():
    result = calculate_fd_maturity(
        principal=1000000, annual_interest_rate=7.0, tenure_days=365, tds_applicable=True
    )
    if result.get("total_interest", 0) > 40000:
        assert result.get("tds_deducted", 0) > 0
        assert result.get("net_maturity_after_tds") < result["maturity_amount"]


def test_fd_no_tds_when_false():
    result = calculate_fd_maturity(
        principal=1000000, annual_interest_rate=7.0, tenure_days=365, tds_applicable=False
    )
    assert result.get("tds_deducted") == 0


def test_fd_all_compounding_options():
    for mode in ["monthly", "quarterly", "half_yearly", "yearly"]:
        result = calculate_fd_maturity(
            principal=100000, annual_interest_rate=6.5, tenure_days=365, compounding=mode
        )
        assert "errors" not in result, f"Failed for compounding={mode}"


def test_fd_yearly_breakdown_present():
    result = calculate_fd_maturity(
        principal=100000, annual_interest_rate=6.5, tenure_days=730, compounding="quarterly"
    )
    assert "yearly_breakdown" in result


def test_fd_zero_tenure():
    result = calculate_fd_maturity(principal=100000, annual_interest_rate=6.5, tenure_days=0)
    assert "errors" in result


def test_fd_negative_principal():
    result = calculate_fd_maturity(principal=-100000, annual_interest_rate=6.5, tenure_days=365)
    assert "errors" in result


def test_fd_invalid_compounding():
    result = calculate_fd_maturity(
        principal=100000, annual_interest_rate=6.5, tenure_days=365, compounding="daily"
    )
    assert "errors" in result
