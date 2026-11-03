"""Fixed Deposit maturity calculator."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = "Submit Form 15G/15H to avoid TDS if income is below taxable limit."


def calculate_fd_maturity(
    principal: float,
    annual_interest_rate: float = 0.0,
    tenure_days: int = 0,
    compounding: str = "quarterly",
    is_senior_citizen: bool = False,
    senior_citizen_bonus: float = 0.25,
    tds_applicable: bool = True,
    financial_year: str = "2025-26",
    **kwargs: Any,
) -> dict[str, Any]:
    """Calculate FD maturity amount.

    Args:
        principal: Deposit amount in INR
        annual_interest_rate: Rate as percentage (e.g., 6.5)
        tenure_days: Deposit tenure in days
        compounding: "monthly","quarterly","half_yearly","yearly","simple"
        is_senior_citizen: Senior citizen flag
        senior_citizen_bonus: Extra rate in percentage points
        tds_applicable: Apply 10% TDS if interest > ₹40,000/yr
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with maturity amount and breakdown.
    """
    is_valid_fy, err_resp = validate_financial_year("fd_maturity", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp
    annual_interest_rate = kwargs.get("annual_rate", annual_interest_rate)

    if "tenure_years" in kwargs and tenure_days == 0:
        tenure_days = kwargs["tenure_years"] * 365

    if "compounding_frequency" in kwargs and compounding == "quarterly":
        freq = kwargs["compounding_frequency"]
        if freq == 12:
            compounding = "monthly"
        elif freq == 4:
            compounding = "quarterly"
        elif freq == 2:
            compounding = "half_yearly"
        elif freq == 1:
            compounding = "yearly"

    errors = []
    if principal <= 0:
        errors.append("principal must be > 0")
    if tenure_days <= 0:
        errors.append("tenure_days must be > 0")
    if compounding not in ("monthly", "quarterly", "half_yearly", "yearly", "simple"):
        errors.append("Invalid compounding type")

    if errors:
        err_res = {"errors": errors, "disclaimer": DISCLAIMER}
        return attach_rule_metadata(err_res, "fd_maturity", financial_year)

    effective_rate = annual_interest_rate + (senior_citizen_bonus if is_senior_citizen else 0)
    t = tenure_days / 365

    n_map = {"monthly": 12, "quarterly": 4, "half_yearly": 2, "yearly": 1}
    n = n_map.get(compounding, 4)

    if compounding == "simple":
        maturity = principal * (1 + effective_rate * t / 100)
    else:
        maturity = principal * (1 + effective_rate / (n * 100)) ** (n * t)

    total_interest = maturity - principal

    annual_interest = total_interest / t if t > 0 else 0
    tds_threshold = 50000 if is_senior_citizen else 40000
    tds_deducted = (
        round(total_interest * 0.10, 2) if tds_applicable and annual_interest > tds_threshold else 0
    )
    net_maturity = maturity - tds_deducted

    res = {
        "principal": principal,
        "effective_rate": effective_rate,
        "tenure_days": tenure_days,
        "maturity_amount": round(maturity, 2),
        "total_interest": round(total_interest, 2),
        "tds_deducted": tds_deducted,
        "net_maturity_after_tds": round(net_maturity, 2),
        "yearly_breakdown": [
            {
                "year": 1,
                "interest_accrued": round(total_interest, 2),
                "cumulative_amount": round(maturity, 2),
            }
        ],
        "disclaimer": DISCLAIMER,
    }
    return attach_rule_metadata(res, "fd_maturity", financial_year)
