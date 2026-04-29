"""Tests for HRA exemption calculator."""

import pytest
from mcp_india_stack.tools.hra import calculate_hra_exemption, calculate_hra_for_salary_structure


def test_hra_metro_full_exemption() -> None:
    """Test HRA when all three conditions yield full exemption."""
    result = calculate_hra_exemption(
        basic_salary=50000,
        hra_received=180000,
        rent_paid=240000,
        city_type="metro",
    )
    assert result["exemption"] == 180000
    assert result["taxable_hra"] == 0


def test_hra_non_metro_full_exemption() -> None:
    """Test HRA non-metro with full exemption."""
    result = calculate_hra_exemption(
        basic_salary=30000,
        hra_received=72000,
        rent_paid=120000,
        city_type="non_metro",
    )
    assert result["exemption"] == 72000
    assert result["taxable_hra"] == 0


def test_hra_partial_exemption() -> None:
    """Test HRA with partial exemption due to rent limit."""
    result = calculate_hra_exemption(
        basic_salary=50000,
        hra_received=180000,
        rent_paid=120000,  # Rent minus 10% salary = 60000, which is less than hra
        city_type="metro",
    )
    assert result["exemption"] == 60000
    assert result["taxable_hra"] == 120000


def test_hra_government_employee() -> None:
    """Test HRA for government employee (simplified formula)."""
    result = calculate_hra_exemption(
        basic_salary=50000,
        hra_received=120000,
        rent_paid=180000,
        is_government_employee=True,
    )
    assert result["exemption"] == 120000
    assert "is_government_employee" in result


def test_hra_monthly_structure() -> None:
    """Test monthly HRA calculation."""
    result = calculate_hra_for_salary_structure(
        monthly_basic=50000,
        monthly_hra=15000,
        monthly_rent=20000,
        city="mumbai",
    )
    assert "monthly_exemption" in result
    assert "monthly_taxable_hra" in result
    assert result["city_type"] == "metro"
