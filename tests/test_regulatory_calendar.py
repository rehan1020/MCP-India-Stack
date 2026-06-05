"""Tests for regulatory calendar."""

from mcp_india_stack.tools.regulatory_calendar import get_regulatory_deadlines


def test_calendar_full_year_no_month():
    result = get_regulatory_deadlines()
    assert result.get("total_deadlines") > 10


def test_calendar_category_filter():
    result = get_regulatory_deadlines(category="Income Tax")
    assert result.get("total_deadlines") > 0


def test_calendar_date_range_filter():
    result = get_regulatory_deadlines(from_date="2025-07-01", to_date="2025-07-31")
    assert result.get("total_deadlines") > 0


def test_calendar_invalid_category():
    result = get_regulatory_deadlines(category="InvalidCategory")
    assert result.get("total_deadlines") == 0


def test_calendar_from_date_only():
    result = get_regulatory_deadlines(from_date="2026-01-01")
    assert result.get("total_deadlines") > 0


def test_calendar_to_date_only():
    result = get_regulatory_deadlines(to_date="2025-07-31")
    assert result.get("total_deadlines") > 0
