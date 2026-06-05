"""Tests for HRA calculator."""

import pytest

from mcp_india_stack.tools.hra import (
    _classify_city,
    calculate_hra_exemption,
    calculate_hra_for_salary_structure,
)


class TestHRABasic:
    def test_basic_calculation(self):
        result = calculate_hra_exemption(
            basic_salary=50000, hra_received=15000, rent_paid=20000, city_type="metro"
        )
        assert "exemption" in result

    def test_metro_city(self):
        result = calculate_hra_exemption(
            basic_salary=50000, hra_received=15000, rent_paid=25000, city_type="metro"
        )
        assert "exemption" in result

    def test_non_metro_city(self):
        result = calculate_hra_exemption(
            basic_salary=50000, hra_received=15000, rent_paid=25000, city_type="non_metro"
        )
        assert "exemption" in result


class TestHRAGovernment:
    def test_government_employee(self):
        result = calculate_hra_exemption(
            basic_salary=50000,
            hra_received=15000,
            rent_paid=20000,
            city_type="metro",
            is_government_employee=True,
        )
        assert "exemption" in result


class TestHRAEdgeCases:
    def test_zero_rent(self):
        result = calculate_hra_exemption(basic_salary=50000, hra_received=15000, rent_paid=0)
        assert result["exemption"] == 0

    def test_rent_below_10_percent(self):
        result = calculate_hra_exemption(basic_salary=50000, hra_received=15000, rent_paid=4000)
        assert result["exemption"] == 0


# ---- Bug 3 regression: metro city classification ----


def test_mumbai_is_metro():
    city_type, warn = _classify_city("Mumbai")
    assert city_type == "metro"
    assert warn is None


def test_delhi_is_metro():
    city_type, warn = _classify_city("Delhi")
    assert city_type == "metro"
    assert warn is None


def test_bangalore_is_not_metro():
    city_type, warn = _classify_city("Bangalore")
    assert city_type == "non_metro"
    assert "40%" in warn


def test_hyderabad_is_not_metro():
    city_type, warn = _classify_city("Hyderabad")
    assert city_type == "non_metro"
    assert warn is not None


def test_pune_is_not_metro():
    city_type, warn = _classify_city("Pune")
    assert city_type == "non_metro"


def test_hra_bangalore_uses_40_pct():
    """Bangalore should use 40% (non-metro) rule, not 50%."""
    result = calculate_hra_for_salary_structure(
        monthly_basic=50_000, monthly_hra=25_000, monthly_rent=30_000, city="Bangalore"
    )
    # Rule 3: 40% of annual basic = ₹2,40,000
    assert result["breakdown"]["50_percent_metro_40_percent_nonmetro"] == pytest.approx(2_40_000)
    assert result["city_type"] == "non_metro"
    # Should have warning about Bangalore
    assert any("Bangalore" in w for w in result.get("warnings", []))


def test_hra_chennai_uses_50_pct():
    """Chennai IS a metro — should use 50%."""
    result = calculate_hra_for_salary_structure(
        monthly_basic=50_000, monthly_hra=25_000, monthly_rent=30_000, city="Chennai"
    )
    assert result["breakdown"]["50_percent_metro_40_percent_nonmetro"] == pytest.approx(3_00_000)
    assert result["city_type"] == "metro"
