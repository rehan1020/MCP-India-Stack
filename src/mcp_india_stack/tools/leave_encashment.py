"""Leave encashment tax calculator under Section 10(10AA)."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = "Taxable portion added to income and taxed at slab rate."


def calculate_leave_encashment_tax(
    leave_encashment_amount: float,
    average_monthly_salary: float,
    earned_leave_balance_days: int,
    years_of_service: int,
    is_government_employee: bool = False,
    financial_year: str = "2025-26",
) -> dict[str, Any]:
    """Calculate tax-exempt portion of leave encashment.

    Args:
        leave_encashment_amount: Actual amount received
        average_monthly_salary: Average of last 10 months basic + DA
        earned_leave_balance_days: Days of earned leave
        years_of_service: Total years of service
        is_government_employee: Government employee flag
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with exemption breakdown.
    """
    is_valid_fy, err_resp = validate_financial_year("leave_encashment", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp

    if leave_encashment_amount <= 0:
        err_res = {"errors": ["leave_encashment_amount must be > 0"], "disclaimer": DISCLAIMER}
        return attach_rule_metadata(err_res, "leave_encashment", financial_year)

    if is_government_employee:
        gov_res = {
            "is_government_employee": True,
            "exemption_amount": leave_encashment_amount,
            "taxable_amount": 0,
            "note": "Government employees: fully exempt under Section 10(10AA)",
            "disclaimer": DISCLAIMER,
        }
        return attach_rule_metadata(gov_res, "leave_encashment", financial_year)

    exemption_1 = leave_encashment_amount
    exemption_2 = average_monthly_salary * 10
    exemption_3 = (average_monthly_salary / 30) * earned_leave_balance_days
    exemption_4 = 2500000

    exemption_amount = min(exemption_1, exemption_2, exemption_3, exemption_4)
    taxable_amount = max(0, leave_encashment_amount - exemption_amount)

    res = {
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
    return attach_rule_metadata(res, "leave_encashment", financial_year)
