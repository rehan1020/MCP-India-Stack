"""SIP returns calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Subject to market risk. Not a guaranteed return product."


def calculate_sip_returns(
    monthly_investment: float,
    expected_annual_return: float,
    tenure_years: int,
    inflation_rate: float = 6.0,
) -> dict[str, Any]:
    """Calculate SIP maturity with inflation-adjusted returns.

    Args:
        monthly_investment: Monthly SIP amount
        expected_annual_return: Expected CAGR %
        tenure_years: Investment tenure
        inflation_rate: Expected inflation %

    Returns:
        Dict with corpus and real returns.
    """
    if monthly_investment <= 0 or tenure_years <= 0:
        return {"errors": ["Invalid parameters"], "disclaimer": DISCLAIMER}

    r = expected_annual_return / (12 * 100)
    n = tenure_years * 12

    corpus = monthly_investment * (((1 + r) ** n - 1) / r) * (1 + r)
    total_invested = monthly_investment * n
    wealth_gained = corpus - total_invested

    real_corpus = corpus / ((1 + inflation_rate / 100) ** tenure_years)

    return {
        "monthly_investment": monthly_investment,
        "expected_annual_return": expected_annual_return,
        "tenure_years": tenure_years,
        "total_invested": round(total_invested, 2),
        "estimated_corpus": round(corpus, 2),
        "wealth_gained": round(wealth_gained, 2),
        "inflation_adjusted_corpus": round(real_corpus, 2),
        "disclaimer": DISCLAIMER,
    }
