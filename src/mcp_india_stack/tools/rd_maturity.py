"""Recurring Deposit maturity calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "RD interest is taxable as per income tax slab."


def calculate_rd_maturity(
    monthly_installment: float,
    annual_interest_rate: float,
    tenure_months: int,
    compounding: str = "quarterly",
) -> dict[str, Any]:
    """Calculate RD maturity amount.

    Args:
        monthly_installment: Monthly deposit amount
        annual_interest_rate: Annual rate as percentage
        tenure_months: Deposit tenure in months
        compounding: Compounding frequency

    Returns:
        Dict with maturity and breakdown.
    """
    if monthly_installment <= 0 or tenure_months <= 0:
        return {"errors": ["Invalid parameters"], "disclaimer": DISCLAIMER}

    r = annual_interest_rate / (4 * 100)
    n = tenure_months // 3

    maturity = monthly_installment * (((1 + r) ** n - 1) / (1 - (1 + r) ** (-1 / 3)))
    total_invested = monthly_installment * tenure_months
    total_interest = maturity - total_invested

    return {
        "monthly_installment": monthly_installment,
        "annual_interest_rate": annual_interest_rate,
        "tenure_months": tenure_months,
        "total_invested": total_invested,
        "maturity_amount": round(maturity, 2),
        "total_interest": round(total_interest, 2),
        "disclaimer": DISCLAIMER,
    }
