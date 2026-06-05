"""Salary restructuring tax optimizer — Section 10 and deduction optimization."""

from __future__ import annotations

from typing import Any

STRUCTURE_OPTIONS = {
    "standard": {
        "description": "Standard salary with basic at 50%",
        "components": ["basic", "hra", "special_allowance"],
    },
    "optimized": {
        "description": "Tax-optimized with higher HRA and LTA",
        "components": ["basic", "hra", "lta", "special_allowance", "children_education"],
    },
    "startup": {
        "description": "Startup-friendly with equity/stock options consideration",
        "components": ["basic", "hra", "special_allowance", "esop", "gratuity"],
    },
}

ALLOWANCE_EXEMPTIONS = {
    "hra": {"section": "Section 10(13A)", "max": "50% of salary if metro, 40% otherwise"},
    "lta": {"section": "Section 10(5)", "max": "Actual travel cost, 2 trips/4 years"},
    "children_education": {
        "section": "Section 10(14)",
        "max": "Fixed 100/child/month (max 2 children)",
    },
    # NOTE: Conveyance (₹19,200) and medical (₹15,000) exemptions abolished from FY2018-19.
    # Standard deduction of ₹50,000/₹75,000 replaced them.
}

DEDUCTION_CATEGORIES = {
    "80c": {
        "max": 150_000,
        "items": ["PPF", "ELSS", "NSC", "Life Insurance", "Home Loan Principal"],
    },
    "80d": {"max": 25_000, "items": ["Medical Insurance - Self"]},
    "80d_family": {"max": 50_000, "items": ["Medical Insurance - Parents (senior)"]},
    "80e": {"max": None, "items": ["Education Loan Interest"]},
    "80g": {"max": None, "items": ["Donations (50-100% deduction)"]},
    "80tta": {"max": 10_000, "items": ["Interest from Savings Account"]},
    "80dd": {"max": 125_000, "items": ["Dependant with disability"]},
    "80u": {"max": 125_000, "items": ["Self disability"]},
    "24": {"max": 200_000, "items": ["Home Loan Interest (self-occupied)"]},
    "16": {"max": 50_000, "items": ["Standard Deduction (old regime)"]},
    "16_new": {"max": 75_000, "items": ["Standard Deduction (new regime FY2025-26)"]},
}


def calculate_salary_restructuring(
    current_gross: float,
    current_basic_ratio: float = 0.50,
    structure_type: str = "standard",
    include_meal_card: bool = False,
    include_wallet_allowance: bool = False,
    has_hra: bool = True,
    rent_in_metro: bool = False,
    family_medical: bool = False,
    parents_medical: bool = False,
) -> dict[str, Any]:
    """Calculate salary restructuring options for tax optimization.

    Args:
        current_gross: Current gross annual salary in INR
        current_basic_ratio: Current basic salary as ratio of gross (0.40-0.60)
        structure_type: Structure option (standard, optimized, startup)
        include_meal_card: Include Sodexo/Food card allowance
        include_wallet_allowance: Include flexible wallet allowance
        has_hra: Employee receives HRA
        rent_in_metro: Rent paid in metro city (higher HRA)
        family_medical: Include family medical insurance
        parents_medical: Include parents medical insurance (additional)

    Returns:
        Tax-optimized salary structure with breakdown
    """
    basic_ratio = current_basic_ratio
    hra_ratio = 0.20 if has_hra else 0

    basic = current_gross * basic_ratio
    hra = current_gross * hra_ratio if has_hra else 0

    # Post FY2018-19: conveyance and medical are NOT separately exempt.
    # Standard deduction covers them in a lump sum.
    special_allowance = current_gross - (basic + hra)

    if special_allowance < 0:
        special_allowance = 0

    restructured = {
        "basic": round(basic, 2),
        "hra": round(hra, 2),
        "special_allowance": round(special_allowance, 2),
    }

    if include_meal_card:
        restructured["meal_card"] = 110_000

    if include_wallet_allowance:
        restructured["wallet_allowance"] = 60_000

    restructured["total"] = sum(restructured.values())

    # Standard deduction: ₹75,000 new regime / ₹50,000 old regime
    standard_deduction = 75_000

    deductions = {
        "standard_deduction": standard_deduction,
        "section_80c": 150_000,
        "section_80d_self": 25_000,
    }

    if family_medical:
        deductions["section_80d_family"] = 25_000
    if parents_medical:
        deductions["section_80d_parents"] = 50_000

    total_deductions = sum(deductions.values())

    taxable_income = current_gross - total_deductions

    estimated_tax = _quick_tax_estimate(taxable_income)

    return {
        "input": {
            "current_gross": current_gross,
            "current_basic_ratio": current_basic_ratio,
            "structure_type": structure_type,
            "rent_in_metro": rent_in_metro,
        },
        "restructured_components": restructured,
        "standard_deduction": standard_deduction,
        "standard_deduction_note": (
            "Standard deduction replaces old transport (₹19,200) and medical (₹15,000) exemptions."
        ),
        "recommended_deductions": deductions,
        "total_deductions": total_deductions,
        "estimated_taxable_income": taxable_income,
        "estimated_annual_tax": estimated_tax,
        "effective_tax_rate": round((estimated_tax / current_gross) * 100, 2)
        if current_gross > 0
        else 0,
        "structure_options": list(STRUCTURE_OPTIONS.keys()),
    }


def _quick_tax_estimate(taxable_income: float) -> float:
    """Quick tax estimate for FY2025-26 new regime."""
    tax = 0.0
    if taxable_income <= 400_000:
        tax = 0.0
    elif taxable_income <= 800_000:
        tax = (taxable_income - 400_000) * 0.05
    elif taxable_income <= 1_200_000:
        tax = 20_000 + (taxable_income - 800_000) * 0.10
    elif taxable_income <= 1_600_000:
        tax = 60_000 + (taxable_income - 1_200_000) * 0.15
    elif taxable_income <= 2_000_000:
        tax = 120_000 + (taxable_income - 1_600_000) * 0.20
    elif taxable_income <= 2_400_000:
        tax = 200_000 + (taxable_income - 2_000_000) * 0.25
    else:
        tax = 300_000 + (taxable_income - 2_400_000) * 0.30

    # BUG FIX: 87A rebate was not being applied for income <= 12L
    if taxable_income <= 1_200_000:
        tax = 0.0

    return tax
