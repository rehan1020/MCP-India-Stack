"""Tests for salary restructuring calculator."""

import pytest

from mcp_india_stack.tools.salary_restructuring import calculate_salary_restructuring


class TestBasicCalculation:
    def test_standard_structure(self):
        result = calculate_salary_restructuring(current_gross=1000000, current_basic_ratio=0.50)
        assert "input" in result
        assert result["input"]["current_gross"] == 1000000

    def test_restructure_components_present(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        assert "restructured_components" in result
        assert "basic" in result["restructured_components"]
        assert "hra" in result["restructured_components"]

    def test_basic_salary_calc(self):
        result = calculate_salary_restructuring(current_gross=1000000, current_basic_ratio=0.50)
        assert result["restructured_components"]["basic"] == 500000

    def test_hra_when_has_hra_true(self):
        result = calculate_salary_restructuring(current_gross=1000000, has_hra=True)
        assert result["restructured_components"]["hra"] == 200000

    def test_hra_when_has_hra_false(self):
        result = calculate_salary_restructuring(current_gross=1000000, has_hra=False)
        assert result["restructured_components"]["hra"] == 0


class TestDeductions:
    def test_recommended_deductions_present(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        assert "recommended_deductions" in result

    def test_total_deductions_calculated(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        # 75000 (SD) + 150000 (80C) + 25000 (80D) = 250000
        assert result["total_deductions"] == 250000

    def test_family_medical_adds_deduction(self):
        result = calculate_salary_restructuring(current_gross=1000000, family_medical=True)
        assert "section_80d_family" in result["recommended_deductions"]

    def test_parents_medical_adds_deduction(self):
        result = calculate_salary_restructuring(current_gross=1000000, parents_medical=True)
        assert "section_80d_parents" in result["recommended_deductions"]


class TestTaxCalculation:
    def test_estimated_taxable_income(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        # 1000000 - 250000 = 750000
        assert result["estimated_taxable_income"] == 750000

    def test_estimated_annual_tax(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        # Tax on 750000 new regime = 0 (due to 87A rebate up to 12L)
        assert result["estimated_annual_tax"] == pytest.approx(0, abs=100)

    def test_effective_tax_rate(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        # Tax on 750000 new regime = 0, effective = 0.0%
        assert result["effective_tax_rate"] == pytest.approx(0.0, abs=0.01)

    def test_zero_tax_low_income(self):
        result = calculate_salary_restructuring(current_gross=300000)
        assert result["estimated_annual_tax"] == 0


class TestStructureOptions:
    def test_structure_options_listed(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        assert "structure_options" in result
        assert "standard" in result["structure_options"]
        assert "optimized" in result["structure_options"]
        assert "startup" in result["structure_options"]


class TestMealCard:
    def test_meal_card_included(self):
        result = calculate_salary_restructuring(current_gross=1000000, include_meal_card=True)
        assert "meal_card" in result["restructured_components"]
        assert result["restructured_components"]["meal_card"] == 110000

    def test_meal_card_not_included_by_default(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        assert "meal_card" not in result["restructured_components"]


class TestTotal:
    def test_total_equals_sum_of_components(self):
        result = calculate_salary_restructuring(current_gross=1000000)
        components = result["restructured_components"]
        expected_total = sum(
            v for k, v in components.items() if k != "total" and isinstance(v, (int, float))
        )
        assert components["total"] == expected_total


# ---- Bug 8 regression: no stale conveyance, standard deduction present ----


def test_salary_restructuring_no_stale_conveyance():
    """Conveyance must not appear as a separate component (abolished FY2018-19)."""
    result = calculate_salary_restructuring(current_gross=20_00_000)
    # No conveyance in restructured components
    assert "conveyance" not in result["restructured_components"]
    # Standard deduction must be present
    assert result.get("standard_deduction") in (50_000, 75_000)


def test_salary_restructuring_standard_deduction_note():
    """Standard deduction note explains replacement of old exemptions."""
    result = calculate_salary_restructuring(current_gross=15_00_000)
    assert "standard_deduction_note" in result
    assert "19,200" in result["standard_deduction_note"]  # mentions old amount


def test_salary_restructuring_no_medical_reimbursement_line():
    """Medical reimbursement (₹15K) not a separate exempt line — covered by SD."""
    result = calculate_salary_restructuring(current_gross=15_00_000)
    assert "medical_reimbursement" not in result["restructured_components"]
