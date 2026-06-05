"""Tests for Section 234A/234B/234C interest calculator."""

import pytest

from mcp_india_stack.tools.income_tax_interest import calculate_income_tax_interest


def test_234a_3months_late():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=50000,
        filing_date="2025-10-31",
        due_date="2025-07-31",
    )
    s = result.get("section_234a", {})
    assert s.get("applicable") is True


def test_234a_filed_on_due_date():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=50000,
        filing_date="2025-07-31",
        due_date="2025-07-31",
    )
    assert result.get("section_234a", {}).get("applicable") is False


def test_234b_triggered_below_90pct():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=0,
        advance_tax_paid={"q1": 0, "q2": 0, "q3": 0, "q4": 50000},
        filing_date="2025-07-31",
        due_date="2025-07-31",
    )
    assert result.get("section_234b", {}).get("applicable") is True


def test_234b_not_triggered_at_90pct():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=0,
        advance_tax_paid={"q1": 50000, "q2": 50000, "q3": 50000, "q4": 30000},
        filing_date="2025-07-31",
        due_date="2025-07-31",
    )
    assert result.get("section_234b", {}).get("applicable") is False


def test_234c_q1_shortfall():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=0,
        advance_tax_paid={"q1": 10000, "q2": 50000, "q3": 50000, "q4": 90000},
        filing_date="2025-07-31",
        due_date="2025-07-31",
    )
    s = result.get("section_234c", {})
    assert s.get("applicable") is True


def test_all_compliant_zero_interest():
    result = calculate_income_tax_interest(
        total_tax_liability=200000,
        tds_deducted=0,
        advance_tax_paid={"q1": 30000, "q2": 60000, "q3": 60000, "q4": 50000},
        filing_date="2025-07-30",
        due_date="2025-07-31",
    )
    assert result.get("total_interest_payable") == 0


def test_total_interest_is_sum_of_sections():
    result = calculate_income_tax_interest(
        total_tax_liability=300000,
        tds_deducted=0,
        advance_tax_paid={"q1": 0, "q2": 0, "q3": 0, "q4": 0},
        filing_date="2025-10-31",
        due_date="2025-07-31",
    )
    d = result
    section_sum = (
        d.get("section_234a", {}).get("interest_amount", 0)
        + d.get("section_234b", {}).get("interest_amount", 0)
        + d.get("section_234c", {}).get("total_234c_interest", 0)
    )
    assert d.get("total_interest_payable") == pytest.approx(section_sum, abs=10)


# ---- Bug 6 regression: cumulative shortfall for 234C ----


def test_234c_all_zero_advance_tax():
    """All quarters missed → cumulative shortfalls for Q1/Q2/Q3."""
    result = calculate_income_tax_interest(
        total_tax_liability=1_00_000,
        advance_tax_paid={},
        tds_deducted=0,
    )
    # Q1: 15K short × 1% × 3 = ₹450
    # Q2: 45K short × 1% × 3 = ₹1,350
    # Q3: 75K short × 1% × 3 = ₹2,250
    total_234c = result["section_234c"]["total_234c_interest"]
    assert total_234c == pytest.approx(450 + 1350 + 2250)


def test_234c_paid_only_in_q2():
    """Q1 nothing, Q2 full 45% — Q1 should still have shortfall interest."""
    result = calculate_income_tax_interest(
        total_tax_liability=1_00_000,
        advance_tax_paid={"q1": 0, "q2": 45_000, "q3": 30_000, "q4": 25_000},
        tds_deducted=0,
    )
    q_shortfalls = result["section_234c"]["quarterly_shortfalls"]
    # Q1 should have shortfall: needed ₹15K cumulative, paid ₹0
    q1_item = q_shortfalls[0]
    assert q1_item["shortfall"] == 15_000
    assert q1_item["interest"] == pytest.approx(450)


def test_234c_q2_catch_up():
    """Paid nothing in Q1, but catch up by Q2. Only Q1 should have interest."""
    result = calculate_income_tax_interest(
        total_tax_liability=1_00_000,
        advance_tax_paid={"q1": 0, "q2": 75_000, "q3": 25_000, "q4": 0},
        tds_deducted=0,
    )
    q_shortfalls = result["section_234c"]["quarterly_shortfalls"]
    # Q1: cumulative paid 0, needed 15K → shortfall
    # Q2: cumulative paid 75K, needed 45K → OK
    # Q3: cumulative paid 100K, needed 75K → OK
    assert len(q_shortfalls) == 1
    assert q_shortfalls[0]["quarter"] == "Q1_Jun15"
