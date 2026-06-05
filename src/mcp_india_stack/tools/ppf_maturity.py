"""PPF (Public Provident Fund) maturity calculator."""

from __future__ import annotations

from typing import Any

MIN_ANNUAL_INVESTMENT = 500
MAX_ANNUAL_INVESTMENT = 150000

DISCLAIMER = (
    "Interest rate used is as notified for FY2025-26. GoI revises PPF rates quarterly. "
    "Verify current rate at https://www.indiapost.gov.in before making investment decisions."
)


def calculate_ppf_maturity(
    annual_investment: float,
    tenure_years: int = 15,
    annual_interest_rate: float = 7.1,
    **kwargs: Any,
) -> dict[str, Any]:
    """Calculate PPF maturity amount with year-by-year breakdown.

    Args:
        annual_investment: Amount invested per year in INR.
        tenure_years: PPF tenure in years (min 15, extendable in blocks of 5).
        annual_interest_rate: Current PPF rate (default 7.1% for FY2025-26).

    Returns:
        Dict with maturity amount, total invested, interest earned, and breakdown.
    """
    try:
        annual_interest_rate = kwargs.get("annual_rate", annual_interest_rate)
        errors: list[str] = []

        if annual_investment < MIN_ANNUAL_INVESTMENT:
            errors.append(f"PPF minimum annual investment is ₹{MIN_ANNUAL_INVESTMENT:,}")
        if annual_investment > MAX_ANNUAL_INVESTMENT:
            errors.append(f"PPF annual investment ceiling is ₹{MAX_ANNUAL_INVESTMENT:,}")

        if tenure_years < 15:
            errors.append("PPF minimum tenure is 15 years")
        if (tenure_years - 15) % 5 != 0:
            errors.append(
                "PPF tenure must be 15 years or extended in 5-year blocks (15, 20, 25, 30)"
            )

        if errors:
            return {
                "annual_investment": annual_investment,
                "tenure_years": tenure_years,
                "annual_interest_rate": annual_interest_rate,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        r = annual_interest_rate / 100

        future_value = annual_investment * (((1 + r) ** tenure_years - 1) / r) * (1 + r)

        maturity_amount = round(future_value, 2)

        total_invested = annual_investment * tenure_years

        total_interest_earned = maturity_amount - total_invested

        effective_return_multiplier = (
            round(maturity_amount / total_invested, 2) if total_invested > 0 else 0
        )

        yearly_breakdown = []
        balance = 0.0

        for year in range(1, tenure_years + 1):
            opening = balance
            investment = annual_investment
            interest = round((opening + investment) * r, 2)
            closing = round(opening + investment + interest, 2)

            yearly_breakdown.append(
                {
                    "year": year,
                    "opening": round(opening, 2),
                    "investment": investment,
                    "interest": interest,
                    "closing": closing,
                }
            )

            balance = closing

        result: dict[str, Any] = {
            "annual_investment": annual_investment,
            "tenure_years": tenure_years,
            "annual_interest_rate": annual_interest_rate,
            "total_invested": total_invested,
            "maturity_amount": maturity_amount,
            "total_interest_earned": round(total_interest_earned, 2),
            "effective_return_multiplier": effective_return_multiplier,
            "tax_status": "EEE — Exempt at investment, accumulation, and maturity",
            "yearly_breakdown": yearly_breakdown,
            "disclaimer": DISCLAIMER,
        }

        return result

    except Exception as exc:
        return {
            "annual_investment": annual_investment
            if isinstance(annual_investment, (int, float))
            else 0,
            "tenure_years": tenure_years if isinstance(tenure_years, int) else 0,
            "annual_interest_rate": annual_interest_rate
            if isinstance(annual_interest_rate, (int, float))
            else 0,
            "errors": [f"PPF calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
