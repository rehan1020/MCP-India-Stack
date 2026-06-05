"""Tests for EMI calculator."""

import pytest

from mcp_india_stack.tools.emi import calculate_emi


class TestEMI:
    def test_home_loan_standard(self) -> None:
        result = calculate_emi(
            principal=5000000,
            annual_interest_rate=8.5,
            tenure_months=240,
            loan_type="home",
        )
        assert result["emi"] == pytest.approx(43391, abs=1)
        assert result["total_interest"] > 0

    def test_zero_interest(self) -> None:
        result = calculate_emi(principal=120000, annual_interest_rate=0, tenure_months=12)
        assert result["emi"] == 10000

    def test_short_tenure(self) -> None:
        result = calculate_emi(principal=100000, annual_interest_rate=12, tenure_months=6)
        assert result["emi"] > 0

    def test_total_interest_positive(self) -> None:
        result = calculate_emi(principal=500000, annual_interest_rate=10, tenure_months=36)
        assert result["total_interest"] >= 0

    def test_invalid_tenure(self) -> None:
        result = calculate_emi(principal=100000, annual_interest_rate=10, tenure_months=400)
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_negative_principal(self) -> None:
        result = calculate_emi(principal=-100000, annual_interest_rate=10, tenure_months=12)
        assert "errors" in result


# --- Bug fix verification tests ---


def test_emi_negative_principal_errors():
    result = calculate_emi(-500_000, 8.5, 240)
    assert result.get("errors")
    assert "principal" in result["errors"][0].lower()
    assert "emi" not in result  # no fallback result


def test_emi_400_months_errors():
    result = calculate_emi(500_000, 14, 400)
    assert result.get("errors")
    assert "360" in result["errors"][0]
    assert "emi" not in result  # no fallback result


def test_emi_zero_principal_errors():
    result = calculate_emi(0, 8.5, 240)
    assert result.get("errors")


def test_emi_negative_rate_errors():
    result = calculate_emi(500_000, -5, 240)
    assert result.get("errors")
    assert "interest rate" in result["errors"][0].lower()


def test_emi_invalid_loan_type_errors():
    result = calculate_emi(500_000, 8.5, 240, loan_type="spaceship")
    assert result.get("errors")
    assert "loan_type" in result["errors"][0].lower()
