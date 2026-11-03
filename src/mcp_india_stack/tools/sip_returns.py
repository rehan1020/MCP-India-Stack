"""SIP returns calculator."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = "Subject to market risk. Not a guaranteed return product."


def calculate_sip_returns(
    monthly_investment: float,
    expected_annual_return: float,
    tenure_years: int,
    inflation_rate: float = 6.0,
    financial_year: str = "2025-26",
) -> dict[str, Any]:
    """Calculate SIP maturity with inflation-adjusted returns.

    Args:
        monthly_investment: Monthly SIP amount
        expected_annual_return: Expected CAGR %
        tenure_years: Investment tenure
        inflation_rate: Expected inflation %
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with corpus and real returns.
    """
    is_valid_fy, err_resp = validate_financial_year("sip_returns", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp

    if monthly_investment <= 0 or tenure_years <= 0:
        err_res = {"errors": ["Invalid parameters"], "disclaimer": DISCLAIMER}
        return attach_rule_metadata(err_res, "sip_returns", financial_year)

    r = expected_annual_return / (12 * 100)
    n = tenure_years * 12

    corpus = monthly_investment * (((1 + r) ** n - 1) / r) * (1 + r)
    total_invested = monthly_investment * n
    wealth_gained = corpus - total_invested

    real_corpus = corpus / ((1 + inflation_rate / 100) ** tenure_years)

    res = {
        "monthly_investment": monthly_investment,
        "expected_annual_return": expected_annual_return,
        "tenure_years": tenure_years,
        "total_invested": round(total_invested, 2),
        "estimated_corpus": round(corpus, 2),
        "wealth_gained": round(wealth_gained, 2),
        "inflation_adjusted_corpus": round(real_corpus, 2),
        "disclaimer": DISCLAIMER,
    }
    return attach_rule_metadata(res, "sip_returns", financial_year)
