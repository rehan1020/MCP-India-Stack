"""Tests for advance tax calculator."""

import pytest

from mcp_india_stack.tools.advance_tax import calculate_advance_tax, calculate_interest_penalty


class TestAdvanceTaxBasic:
    def test_low_income_below_10k(self):
        result = calculate_advance_tax(estimated_income=200000)
        assert result["is_advance_tax_required"] is False
        assert result["advance_tax_due"] == 0.0

    def test_high_income_above_10k(self):
        result = calculate_advance_tax(estimated_income=1500000)
        assert result["is_advance_tax_required"] is True
        assert result["advance_tax_due"] > 0

    def test_with_existing_tds(self):
        result = calculate_advance_tax(estimated_income=1500000, existing_tds=50000)
        assert result["existing_tds"] == 50000
        assert result["net_tax_liability"] >= 0


class TestAdvanceTaxInstallments:
    def test_four_installments_present(self):
        result = calculate_advance_tax(estimated_income=1500000)
        assert len(result["installments"]) == 4
        assert result["installments"][0]["quarter"] == "Q1"
        assert result["installments"][1]["quarter"] == "Q2"
        assert result["installments"][2]["quarter"] == "Q3"
        assert result["installments"][3]["quarter"] == "Q4"

    def test_installment_percentages(self):
        result = calculate_advance_tax(estimated_income=1500000)
        assert result["installments"][0]["percentage"] == 15
        assert result["installments"][1]["percentage"] == 45
        assert result["installments"][2]["percentage"] == 75
        assert result["installments"][3]["percentage"] == 100

    def test_installment_amounts_sum_to_total(self):
        """Incremental installment amounts should sum to total advance tax due."""
        result = calculate_advance_tax(estimated_income=1500000)
        total = sum(i["installment_amount"] for i in result["installments"])
        assert total == pytest.approx(result["advance_tax_due"], abs=1)


class TestAdvanceTaxRegime:
    def test_new_regime(self):
        result = calculate_advance_tax(estimated_income=1500000, regime="new")
        assert result["regime"] == "new"

    def test_old_regime(self):
        result = calculate_advance_tax(estimated_income=1000000, regime="old")
        assert "regime" in result


class TestAdvanceTaxInvalid:
    def test_zero_income(self):
        result = calculate_advance_tax(estimated_income=0)
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_negative_income(self):
        result = calculate_advance_tax(estimated_income=-100000)
        assert "errors" in result

    def test_negative_tds(self):
        result = calculate_advance_tax(estimated_income=1500000, existing_tds=-10000)
        assert "errors" in result


class TestInterestPenalty:
    def test_interest_calculation(self):
        result = calculate_interest_penalty(installment_amount=10000, days_late=30)
        assert result["interest_penalty"] > 0
        assert result["months_late"] == 1.0

    def test_zero_days_late(self):
        result = calculate_interest_penalty(installment_amount=10000, days_late=0)
        assert result["interest_penalty"] == 0

    def test_custom_rate(self):
        result = calculate_interest_penalty(
            installment_amount=10000, days_late=30, rate_per_month=2.0
        )
        assert result["interest_penalty"] == 200

    def test_max_3_months(self):
        result = calculate_interest_penalty(installment_amount=10000, days_late=200)
        assert result["months_late"] == 3.0

    def test_negative_installment(self):
        result = calculate_interest_penalty(installment_amount=-1000, days_late=30)
        assert "errors" in result

    def test_negative_days(self):
        result = calculate_interest_penalty(installment_amount=10000, days_late=-10)
        assert "errors" in result


# --- Bug fix verification tests ---


def test_advance_tax_uses_provided_liability():
    """When tax_liability is provided, use it directly without recomputation."""
    result = calculate_advance_tax(tax_liability=2_40_000)
    assert result["installments"][0]["installment_amount"] == 36_000  # 15%
    assert result["installments"][3]["cumulative_amount"] == 2_40_000  # 100%


def test_advance_tax_q4_never_exceeds_liability():
    result = calculate_advance_tax(tax_liability=1_00_000)
    assert result["installments"][3]["cumulative_amount"] <= 1_00_000


# ---- Bug 7 regression: incremental vs cumulative amounts ----


def test_advance_tax_incremental_amounts():
    """Installment amounts should be incremental (what to pay each quarter)."""
    result = calculate_advance_tax(tax_liability=2_40_000)
    q1, q2, q3, q4 = result["installments"]
    assert q1["installment_amount"] == 36_000  # 15%
    assert q2["installment_amount"] == 72_000  # 30%
    assert q3["installment_amount"] == 72_000  # 30%
    assert q4["installment_amount"] == 60_000  # 25%
    # Cumulative totals
    assert q2["cumulative_amount"] == 1_08_000  # 45%
    assert q4["cumulative_amount"] == 2_40_000  # 100%
    # All installments sum to total
    total = sum(i["installment_amount"] for i in result["installments"])
    assert total == 2_40_000


def test_advance_tax_amount_is_incremental():
    """The 'amount' field should be the incremental, not cumulative."""
    result = calculate_advance_tax(tax_liability=1_00_000)
    q2 = result["installments"][1]
    # amount should be 30% incremental (30K), not 45% cumulative (45K)
    assert q2["amount"] == 30_000
    assert q2["cumulative_amount"] == 45_000
