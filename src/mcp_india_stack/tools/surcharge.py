"""Surcharge calculator — standalone tool that imports rates from income_tax.py."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.income_tax import (
    NEW_REGIME_MAX_SURCHARGE,
    SURCHARGE_RATES,
)

DISCLAIMER = (
    "Surcharge computation is based on FY2025-26 rates. "
    "This is an estimate — consult a CA for accurate filing."
)


def _get_surcharge_rate(total_income: float, regime: str) -> float:
    """Determine applicable surcharge rate from SURCHARGE_RATES."""
    rate = 0.0
    for limit, r in SURCHARGE_RATES:
        if total_income <= limit:
            rate = r
            break
        rate = r

    if regime == "new" and rate > NEW_REGIME_MAX_SURCHARGE:
        rate = NEW_REGIME_MAX_SURCHARGE
    return rate


def calculate_surcharge(
    total_income: float,
    base_tax: float,
    regime: str,
) -> dict[str, Any]:
    """Calculate surcharge and marginal relief for a given income and base tax.

    This is the same surcharge logic used internally by calculate_income_tax,
    exposed as a standalone MCP tool for users who need just the surcharge.

    Args:
        total_income: Total income in rupees.
        base_tax: Base tax amount before surcharge.
        regime: "new" or "old".

    Returns:
        Dict with surcharge breakdown including marginal relief.
    """
    try:
        errors: list[str] = []

        if total_income is None or not isinstance(total_income, (int, float)):
            errors.append("total_income is required and must be a number")
        elif total_income < 0:
            errors.append("total_income cannot be negative")

        if base_tax is None or not isinstance(base_tax, (int, float)):
            errors.append("base_tax is required and must be a number")
        elif base_tax < 0:
            errors.append("base_tax cannot be negative")

        if regime not in ("new", "old"):
            errors.append("regime must be 'new' or 'old'")

        if errors:
            return {
                "financial_year": "2025-26",
                "total_income": total_income if isinstance(total_income, (int, float)) else 0,
                "base_tax": base_tax if isinstance(base_tax, (int, float)) else 0,
                "surcharge_rate": 0,
                "surcharge_before_relief": 0,
                "marginal_relief": 0,
                "surcharge_after_relief": 0,
                "cess_base": 0,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        surcharge_rate = _get_surcharge_rate(total_income, regime)
        surcharge_before_relief = round(base_tax * surcharge_rate, 2)
        marginal_relief = 0.0

        # Marginal relief computation
        if surcharge_rate > 0:
            # Find the threshold that was just crossed
            prev_threshold = 0.0
            prev_surcharge_rate = 0.0
            for limit, rate in SURCHARGE_RATES:
                effective_rate = rate
                if regime == "new" and effective_rate > NEW_REGIME_MAX_SURCHARGE:
                    effective_rate = NEW_REGIME_MAX_SURCHARGE
                if total_income <= limit:
                    break
                prev_threshold = limit
                prev_surcharge_rate = effective_rate

            if prev_threshold > 0:
                excess_income = total_income - prev_threshold
                tax_plus_surcharge = base_tax + surcharge_before_relief
                tax_plus_prev_surcharge = base_tax + round(base_tax * prev_surcharge_rate, 2)
                marginal_limit = tax_plus_prev_surcharge + excess_income

                if tax_plus_surcharge > marginal_limit:
                    marginal_relief = round(tax_plus_surcharge - marginal_limit, 2)
                    if marginal_relief < 0:
                        marginal_relief = 0.0

        surcharge_after_relief = round(surcharge_before_relief - marginal_relief, 2)
        if surcharge_after_relief < 0:
            surcharge_after_relief = 0.0

        cess_base = round(base_tax + surcharge_after_relief, 2)

        return {
            "financial_year": "2025-26",
            "total_income": total_income,
            "base_tax": base_tax,
            "surcharge_rate": surcharge_rate,
            "surcharge_before_relief": surcharge_before_relief,
            "marginal_relief": marginal_relief,
            "surcharge_after_relief": surcharge_after_relief,
            "cess_base": cess_base,
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "financial_year": "2025-26",
            "total_income": total_income if isinstance(total_income, (int, float)) else 0,
            "base_tax": base_tax if isinstance(base_tax, (int, float)) else 0,
            "surcharge_rate": 0,
            "surcharge_before_relief": 0,
            "marginal_relief": 0,
            "surcharge_after_relief": 0,
            "cess_base": 0,
            "errors": [f"Surcharge calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
