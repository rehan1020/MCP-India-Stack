"""Home vs Rent comparison calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Financial model only. Consult a financial advisor before making property decisions."


def calculate_home_vs_rent(
    home_price: float,
    down_payment_percent: float = 20.0,
    loan_interest_rate: float = 8.5,
    loan_tenure_years: int = 20,
    monthly_rent: float = 25000,
    annual_rent_increase: float = 5.0,
    expected_property_appreciation: float = 6.0,
    investment_return: float = 12.0,
    stamp_duty_percent: float = 5.0,
    registration_percent: float = 1.0,
    annual_maintenance_percent: float = 0.5,
    analysis_years: int = 20,
) -> dict[str, Any]:
    """Compare buying vs renting financial outcome.

    Args:
        home_price: Property price in INR
        down_payment_percent: Down payment as %
        loan_interest_rate: Home loan interest rate %
        loan_tenure_years: Loan tenure
        monthly_rent: Current monthly rent
        annual_rent_increase: Expected rent increase %/year
        expected_property_appreciation: Property value appreciation %/year
        investment_return: Return on invested down payment %
        stamp_duty_percent: Stamp duty %
        registration_percent: Registration fee %
        annual_maintenance_percent: Maintenance cost % of property
        analysis_years: Years to compare

    Returns:
        Dict with buy/rent comparison and break-even analysis.
    """
    if down_payment_percent < 10:
        return {
            "errors": ["Down payment must be at least 10% (RBI LTV mandate)"],
            "disclaimer": DISCLAIMER,
        }

    if analysis_years > 30:
        analysis_years = 30

    down_payment = home_price * (down_payment_percent / 100)
    stamp_duty = home_price * (stamp_duty_percent / 100)
    registration = home_price * (registration_percent / 100)
    upfront_cost = down_payment + stamp_duty + registration

    loan_amount = home_price - down_payment
    monthly_rate = loan_interest_rate / (12 * 100)
    n = loan_tenure_years * 12
    emi = loan_amount * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)

    yearly_comparison = []
    buy_equity = home_price
    rent_corpus = upfront_cost

    for year in range(1, analysis_years + 1):
        property_value = home_price * ((1 + expected_property_appreciation / 100) ** year)

        if year <= loan_tenure_years:
            remaining_loan = loan_amount * (1 - year / loan_tenure_years)
            buy_equity = property_value - remaining_loan
        else:
            buy_equity = property_value

        rent_corpus = (rent_corpus + upfront_cost) * (1 + investment_return / 100)

        ahead = "buy" if buy_equity > rent_corpus else "rent"
        yearly_comparison.append(
            {
                "year": year,
                "buy_net_equity": round(buy_equity),
                "rent_corpus": round(rent_corpus),
                "ahead": ahead,
            }
        )

    break_even_year = next((y["year"] for y in yearly_comparison if y["ahead"] == "buy"), None)

    verdict = (
        f"Buying becomes financially better after year {break_even_year}"
        if break_even_year
        else "Renting remains financially better"
    )

    return {
        "home_price": home_price,
        "buy_scenario": {
            "upfront_cost": round(upfront_cost, 2),
            "monthly_emi": round(emi, 2),
            "property_value_at_analysis_end": round(buy_equity, 2),
            "net_equity_at_analysis_end": round(buy_equity, 2),
        },
        "rent_scenario": {
            "rent_at_analysis_end": round(
                monthly_rent * 12 * ((1 + annual_rent_increase / 100) ** (analysis_years - 1)), 2
            ),
            "total_corpus_at_analysis_end": round(rent_corpus, 2),
        },
        "break_even_year": break_even_year,
        "verdict": verdict,
        "yearly_comparison": yearly_comparison,
        "disclaimer": DISCLAIMER,
    }
