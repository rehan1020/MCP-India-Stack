"""Gratuity calculator under the Payment of Gratuity Act, 1972."""

from __future__ import annotations

from typing import Any

GRATUITY_TAX_CEILING = 2000000
MIN_SERVICE_YEARS = 5

DISCLAIMER = (
    "Payable on resignation/retirement after 5 years, or on death/disablement. "
    "Consult a CA for exact computation."
)


def calculate_gratuity(
    last_drawn_salary: float,
    years_of_service: float,
    is_covered_under_act: bool = True,
) -> dict[str, Any]:
    """Calculate gratuity amount under the Payment of Gratuity Act.

    Args:
        last_drawn_salary: Last basic salary + DA per month in INR.
        years_of_service: Total years served (e.g., 5.8 = 5 yrs 9 months).
        is_covered_under_act: True if establishment has 10+ employees.

    Returns:
        Dict with gratuity calculation and tax-exempt breakdown.
    """
    try:
        errors: list[str] = []

        if last_drawn_salary <= 0:
            errors.append("last_drawn_salary must be greater than 0")
        if years_of_service <= 0:
            errors.append("years_of_service must be greater than 0")

        if errors:
            return {
                "last_drawn_salary": last_drawn_salary,
                "years_of_service": years_of_service,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        fractional_part = years_of_service - int(years_of_service)
        if fractional_part >= 0.5:
            completed_years = int(years_of_service) + 1
        else:
            completed_years = int(years_of_service)

        if is_covered_under_act:
            divisor = 26
            formula_used = "Salary × 15 × Years / 26"
        else:
            divisor = 30
            formula_used = "Salary × 15 × Years / 30"

        gratuity_amount = (last_drawn_salary * 15 * completed_years) / divisor

        minimum_service_met = completed_years >= MIN_SERVICE_YEARS

        taxable_gratuity = max(0, gratuity_amount - GRATUITY_TAX_CEILING)

        result: dict[str, Any] = {
            "last_drawn_salary": last_drawn_salary,
            "years_of_service": years_of_service,
            "completed_years_for_calculation": completed_years,
            "is_covered_under_act": is_covered_under_act,
            "gratuity_amount": round(gratuity_amount, 2),
            "tax_exempt_limit": GRATUITY_TAX_CEILING,
            "taxable_gratuity": round(taxable_gratuity, 2),
            "minimum_service_met": minimum_service_met,
            "formula_used": formula_used,
            "disclaimer": DISCLAIMER,
        }

        return result

    except Exception as exc:
        return {
            "last_drawn_salary": last_drawn_salary
            if isinstance(last_drawn_salary, (int, float))
            else 0,
            "years_of_service": years_of_service
            if isinstance(years_of_service, (int, float))
            else 0,
            "errors": [f"Gratuity calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
