"""Sukanya Samriddhi Yojana (SSY) and Senior Citizen Savings Scheme (SCSS) calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Rate as notified for FY2025-26. GoI revises quarterly."


def calculate_sukanya_samriddhi(
    scheme: str,
    annual_investment: float,
    annual_interest_rate: float = 8.2,
) -> dict[str, Any]:
    """Calculate SSY or SCSS maturity.

    Args:
        scheme: "ssy" or "scss"
        annual_investment: Annual deposit amount
        annual_interest_rate: Interest rate (default 8.2%)

    Returns:
        Dict with maturity calculation.
    """
    errors = []
    if scheme not in ("ssy", "scss"):
        errors.append("scheme must be 'ssy' or 'scss'")
    if annual_investment <= 0:
        errors.append("annual_investment must be > 0")

    if errors:
        return {"errors": errors, "disclaimer": DISCLAIMER}

    if scheme == "ssy":
        if annual_investment < 250:
            return {"errors": ["SSY minimum is ₹250"], "disclaimer": DISCLAIMER}
        if annual_investment > 150000:
            return {"errors": ["SSY maximum is ₹1,50,000"], "disclaimer": DISCLAIMER}

        r = annual_interest_rate / 100
        maturity = annual_investment * (((1 + r) ** 15 - 1) / r) * (1 + r)
        total_invested = annual_investment * 15

        return {
            "scheme": "ssy",
            "annual_investment": annual_investment,
            "maturity_amount": round(maturity, 2),
            "total_invested": total_invested,
            "total_interest": round(maturity - total_invested, 2),
            "tax_status": "EEE — fully exempt",
            "disclaimer": DISCLAIMER,
        }

    else:  # SCSS
        if annual_investment > 3000000:
            return {"errors": ["SCSS maximum is ₹30,00,000"], "disclaimer": DISCLAIMER}

        total_interest = annual_investment * (annual_interest_rate / 100) * 5
        maturity = annual_investment + total_interest

        return {
            "scheme": "scss",
            "annual_investment": annual_investment,
            "maturity_amount": round(maturity, 2),
            "total_invested": annual_investment,
            "total_interest": round(total_interest, 2),
            "tax_note": "Interest is taxable. TDS applicable if interest > ₹50,000/quarter.",
            "disclaimer": DISCLAIMER,
        }
