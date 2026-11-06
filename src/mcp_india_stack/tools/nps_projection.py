"""NPS projection calculator."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = (
    "Projection based on constant return assumption. Actual NPS returns vary by fund allocation."
)


def calculate_nps_projection(
    monthly_contribution: float,
    current_age: int,
    retirement_age: int = 60,
    expected_annual_return: float = 10.0,
    annuity_rate: float = 6.0,
    annuity_percent: float = 40.0,
    financial_year: str = "2025-26",
) -> dict[str, Any]:
    """Calculate NPS corpus and monthly pension at retirement.

    Args:
        monthly_contribution: Monthly NPS contribution
        current_age: Current age
        retirement_age: Retirement age (default 60)
        expected_annual_return: Expected annual return %
        annuity_rate: Annuity rate %
        annuity_percent: % of corpus to buy annuity (min 40%)
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with projected corpus and pension.
    """
    is_valid_fy, err_resp = validate_financial_year("nps_projection", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp

    if current_age >= retirement_age:
        err_res = {
            "errors": ["current_age must be less than retirement_age"],
            "disclaimer": DISCLAIMER,
        }
        return attach_rule_metadata(err_res, "nps_projection", financial_year)

    tenure_years = retirement_age - current_age
    r = expected_annual_return / (12 * 100)
    n = tenure_years * 12

    corpus = monthly_contribution * (((1 + r) ** n - 1) / r) * (1 + r)

    lump_sum_withdrawable = corpus * (1 - annuity_percent / 100)
    annuity_corpus = corpus * (annuity_percent / 100)
    monthly_pension = (annuity_corpus * annuity_rate / 100) / 12

    res = {
        "monthly_contribution": monthly_contribution,
        "tenure_years": tenure_years,
        "projected_corpus": round(corpus, 2),
        "lump_sum_withdrawable": round(lump_sum_withdrawable, 2),
        "estimated_monthly_pension": round(monthly_pension, 2),
        "tax_note": "60% lump sum is tax-free. Pension is taxable as per slab.",
        "disclaimer": DISCLAIMER,
    }
    return attach_rule_metadata(res, "nps_projection", financial_year)
