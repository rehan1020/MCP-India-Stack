"""Tests for leave encashment tax calculator."""

import pytest

from mcp_india_stack.tools.leave_encashment import calculate_leave_encashment_tax


def test_govt_employee_fully_exempt():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=1000000,
        average_monthly_salary=50000,
        earned_leave_balance_days=300,
        years_of_service=20,
        is_government_employee=True,
    )
    assert result.get("taxable_amount") == 0
    assert result.get("exemption_amount") == pytest.approx(1000000, abs=1)


def test_ten_months_cap_binding():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=1000000,
        average_monthly_salary=50000,
        earned_leave_balance_days=600,
        years_of_service=10,
        is_government_employee=False,
    )
    assert result.get("exemption_calculations", {}).get("ten_months_salary") == 500000


def test_statutory_ceiling_25_lakh():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=30000000,
        average_monthly_salary=500000,
        earned_leave_balance_days=600,
        years_of_service=30,
        is_government_employee=False,
    )
    assert result.get("exemption_amount") <= 2500000


def test_taxable_plus_exempt_equals_total():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=800000,
        average_monthly_salary=50000,
        earned_leave_balance_days=300,
        years_of_service=10,
    )
    d = result
    assert d.get("taxable_amount", 0) + d.get("exemption_amount", 0) == pytest.approx(800000, abs=1)


def test_zero_taxable_when_exempt_covers_all():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=100000,
        average_monthly_salary=50000,
        earned_leave_balance_days=60,
        years_of_service=5,
    )
    assert result.get("taxable_amount") == 0


def test_negative_encashment_invalid():
    result = calculate_leave_encashment_tax(
        leave_encashment_amount=-100000,
        average_monthly_salary=50000,
        earned_leave_balance_days=100,
        years_of_service=5,
    )
    assert "errors" in result
