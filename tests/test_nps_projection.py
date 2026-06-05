"""Tests for NPS corpus projection."""

import pytest

from mcp_india_stack.tools.nps_projection import calculate_nps_projection


def test_nps_basic_projection():
    result = calculate_nps_projection(monthly_contribution=5000, current_age=30, retirement_age=60)
    assert result.get("projected_corpus") > 0
    assert result.get("estimated_monthly_pension") > 0


def test_nps_lump_sum_plus_annuity_equals_corpus():
    result = calculate_nps_projection(
        monthly_contribution=5000, current_age=30, retirement_age=60, annuity_percent=40
    )
    d = result
    total = d["lump_sum_withdrawable"] + (d["projected_corpus"] * 0.4)
    assert total == pytest.approx(d["projected_corpus"], rel=0.1)


def test_nps_annuity_minimum_40pct():
    result = calculate_nps_projection(
        monthly_contribution=5000, current_age=30, retirement_age=60, annuity_percent=40
    )
    assert result.get("projected_corpus") > 0


def test_nps_longer_tenure_higher_corpus():
    short = calculate_nps_projection(monthly_contribution=5000, current_age=40, retirement_age=60)
    long = calculate_nps_projection(monthly_contribution=5000, current_age=30, retirement_age=60)
    assert long["projected_corpus"] > short["projected_corpus"]


def test_nps_higher_contribution_higher_corpus():
    low = calculate_nps_projection(monthly_contribution=3000, current_age=30, retirement_age=60)
    high = calculate_nps_projection(monthly_contribution=10000, current_age=30, retirement_age=60)
    assert high["projected_corpus"] > low["projected_corpus"]


def test_nps_retirement_before_current_age():
    result = calculate_nps_projection(monthly_contribution=5000, current_age=65, retirement_age=60)
    assert "errors" in result


def test_nps_zero_contribution():
    result = calculate_nps_projection(monthly_contribution=0, current_age=30, retirement_age=60)
    assert "errors" not in result
    assert result.get("projected_corpus") == 0


def test_nps_tax_note_in_response():
    result = calculate_nps_projection(monthly_contribution=5000, current_age=30, retirement_age=60)
    assert "tax" in str(result).lower() or "lump" in str(result).lower()
