"""Step-up SIP calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Returns estimated at constant CAGR. Actual returns vary."


def calculate_step_up_sip(
    initial_monthly_investment: float,
    annual_step_up_percent: float,
    expected_annual_return: float,
    tenure_years: int,
) -> dict[str, Any]:
    """Calculate SIP with annual step-up increment.

    Args:
        initial_monthly_investment: Starting SIP amount
        annual_step_up_percent: % increase each year
        expected_annual_return: Expected CAGR %
        tenure_years: Investment tenure

    Returns:
        Dict comparing step-up vs flat SIP.
    """
    if initial_monthly_investment <= 0:
        return {"errors": ["Initial monthly investment must be > 0"], "disclaimer": DISCLAIMER}
    if tenure_years <= 0 or tenure_years > 50:
        return {"errors": ["Tenure must be between 1 and 50 years"], "disclaimer": DISCLAIMER}
    if expected_annual_return < 0 or expected_annual_return > 100:
        return {
            "errors": ["Expected annual return must be between 0 and 100"],
            "disclaimer": DISCLAIMER,
        }

    monthly_rate = expected_annual_return / 100 / 12
    # Uses simple monthly rate (annual_rate / 12), consistent with standard
    # Indian mutual fund SIP calculators. Geometric equivalent would be
    # (1 + annual_rate/100)^(1/12) - 1, yielding ~3-6% lower corpus over 20yr.
    # Do NOT "fix" this to geometric without updating the test band in
    # tests/test_manual_suite_v2.py (class TestStepUpSIP).
    total_months = tenure_years * 12
    step_up_factor = 1 + annual_step_up_percent / 100

    corpus = 0.0
    total_invested = 0.0
    monthly_sip = initial_monthly_investment

    for year in range(tenure_years):
        for month in range(12):
            months_remaining = total_months - (year * 12 + month)
            # Each installment grows for its remaining tenure
            if monthly_rate > 0:
                fv = monthly_sip * (1 + monthly_rate) ** months_remaining
            else:
                fv = monthly_sip  # 0% return edge case
            corpus += fv
            total_invested += monthly_sip
        monthly_sip *= step_up_factor  # step up once per year

    final_monthly_sip = initial_monthly_investment * (step_up_factor**tenure_years)
    wealth_gained = corpus - total_invested

    # Flat SIP comparison (no step-up, same return)
    flat_corpus = 0.0
    for m in range(total_months):
        months_rem = total_months - m
        if monthly_rate > 0:
            flat_corpus += initial_monthly_investment * (1 + monthly_rate) ** months_rem
        else:
            flat_corpus += initial_monthly_investment

    return {
        "initial_monthly_investment": initial_monthly_investment,
        "annual_step_up_percent": annual_step_up_percent,
        "expected_annual_return": expected_annual_return,
        "tenure_years": tenure_years,
        "final_monthly_sip": round(final_monthly_sip, 2),
        "total_invested": round(total_invested, 2),
        "estimated_corpus": round(corpus, 2),
        "wealth_gained": round(wealth_gained, 2),
        "flat_sip_corpus": round(flat_corpus, 2),
        "step_up_advantage": round(corpus - flat_corpus, 2),
        "disclaimer": DISCLAIMER,
    }
