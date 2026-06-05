"""Leave encashment tax calculator under Section 10(10AA)."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Taxable portion added to income and taxed at slab rate."


def calculate_leave_encashment_tax(
    leave_encashment_amount: float,
    average_monthly_salary: float,
    earned_leave_balance_days: int,
    years_of_service: int,
    is_government_employee: bool = False,
) -> dict[str, Any]:
    """Calculate tax-exempt portion of leave encashment.

    Args:
        leave_encashment_amount: Actual amount received
        average_monthly_salary: Average of last 10 months basic + DA
        earned_leave_balance_days: Days of earned leave
        years_of_service: Total years of service
        is_government_employee: Government employee flag

    Returns:
        Dict with exemption breakdown.
    """
    if leave_encashment_amount <= 0:
        return {"errors": ["leave_encashment_amount must be > 0"], "disclaimer": DISCLAIMER}

    if is_government_employee:
        return {
            "is_government_employee": True,
            "exemption_amount": leave_encashment_amount,
            "taxable_amount": 0,
            "note": "Government employees: fully exempt under Section 10(10AA)",
            "disclaimer": DISCLAIMER,
        }

    exemption_1 = leave_encashment_amount
    exemption_2 = average_monthly_salary * 10
    exemption_3 = (average_monthly_salary / 30) * earned_leave_balance_days
    exemption_4 = 2500000

    exemption_amount = min(exemption_1, exemption_2, exemption_3, exemption_4)
    taxable_amount = max(0, leave_encashment_amount - exemption_amount)

    return {
        "is_government_employee": False,
        "exemption_calculations": {
            "actual_received": leave_encashment_amount,
            "ten_months_salary": exemption_2,
            "daily_rate_based": exemption_3,
            "statutory_ceiling": exemption_4,
        },
        "exemption_amount": round(exemption_amount, 2),
        "taxable_amount": round(taxable_amount, 2),
        "disclaimer": DISCLAIMER,
    }
