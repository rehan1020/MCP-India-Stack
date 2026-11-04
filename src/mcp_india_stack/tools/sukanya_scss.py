"""Sukanya Samriddhi Yojana (SSY) and Senior Citizen Savings Scheme (SCSS) calculator."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = "Rate as notified for FY2025-26. GoI revises quarterly."


def calculate_sukanya_samriddhi(
    scheme: str,
    annual_investment: float,
    annual_interest_rate: float = 8.2,
    financial_year: str = "2025-26",
) -> dict[str, Any]:
    """Calculate SSY or SCSS maturity.

    Args:
        scheme: "ssy" or "scss"
        annual_investment: Annual deposit amount
        annual_interest_rate: Interest rate (default 8.2%)
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with maturity calculation.
    """
    is_valid_fy, err_resp = validate_financial_year("sukanya_samriddhi", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp

    errors = []
    if scheme not in ("ssy", "scss"):
        errors.append("scheme must be 'ssy' or 'scss'")
    if annual_investment <= 0:
        errors.append("annual_investment must be > 0")

    if errors:
        return attach_rule_metadata(
            {"errors": errors, "disclaimer": DISCLAIMER},
            "sukanya_samriddhi",
            financial_year,
        )

    if scheme == "ssy":
        if annual_investment < 250:
            return attach_rule_metadata(
                {"errors": ["SSY minimum is ₹250"], "disclaimer": DISCLAIMER},
                "sukanya_samriddhi",
                financial_year,
            )
        if annual_investment > 150000:
            return attach_rule_metadata(
                {"errors": ["SSY maximum is ₹1,50,000"], "disclaimer": DISCLAIMER},
                "sukanya_samriddhi",
                financial_year,
            )

        r = annual_interest_rate / 100
        maturity = annual_investment * (((1 + r) ** 15 - 1) / r) * (1 + r)
        total_invested = annual_investment * 15

        res_ssy = {
            "scheme": "ssy",
            "annual_investment": annual_investment,
            "maturity_amount": round(maturity, 2),
            "total_invested": total_invested,
            "total_interest": round(maturity - total_invested, 2),
            "tax_status": "EEE — fully exempt",
            "disclaimer": DISCLAIMER,
        }
        return attach_rule_metadata(res_ssy, "sukanya_samriddhi", financial_year)

    else:  # SCSS
        if annual_investment > 3000000:
            return attach_rule_metadata(
                {"errors": ["SCSS maximum is ₹30,00,000"], "disclaimer": DISCLAIMER},
                "sukanya_samriddhi",
                financial_year,
            )

        total_interest = annual_investment * (annual_interest_rate / 100) * 5
        maturity = annual_investment + total_interest

        res_scss = {
            "scheme": "scss",
            "annual_investment": annual_investment,
            "maturity_amount": round(maturity, 2),
            "total_invested": annual_investment,
            "total_interest": round(total_interest, 2),
            "tax_note": "Interest is taxable. TDS applicable if interest > ₹50,000/quarter.",
            "disclaimer": DISCLAIMER,
        }
        return attach_rule_metadata(res_scss, "sukanya_samriddhi", financial_year)
