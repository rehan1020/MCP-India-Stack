"""Capital gains calculator for Indian income tax."""

from __future__ import annotations

from typing import Any


LTCG_EQUITY_EXEMPTION = 100000  # ₹1,00,000 per year (Section 112A)


def calculate_capital_gains(
    sale_price: float = 0,
    purchase_price: float = 0,
    asset_type: str = "equity",
    holding_period_days: int = 365,
    inflation_index_purchase: float | None = None,
    inflation_index_sale: float | None = None,
    expenses_on_sale: float = 0,
    improvements: float = 0,
    quantity: int = 1,
    buy_price: float | None = None,
    sell_price: float | None = None,
    holding_days: int | None = None,
) -> dict[str, Any]:
    """Calculate capital gains for various asset types.

    Args:
        sale_price: Sale proceeds total (after expenses).
        purchase_price: Original purchase price total.
        asset_type: 'equity', 'mutual_fund', 'real_estate', 'gold', 'debentures', 'crypto'.
        holding_period_days: Days held before sale.
        inflation_index_purchase: CII for purchase year (for indexation).
        inflation_index_sale: CII for sale year (for indexation).
        expenses_on_sale: Brokerage, registration, etc.
        improvements: Cost of improvements (for real estate).
        quantity: Number of units (used with buy_price/sell_price).
        buy_price: Per-unit purchase price (alternative to purchase_price).
        sell_price: Per-unit sale price (alternative to sale_price).
        holding_days: Alias for holding_period_days.

    Returns:
        Dict with gains, tax rates, exemption eligibility, and tax liability.
    """
    if buy_price is not None and sell_price is not None and quantity is not None:
        sale_price = sell_price * quantity
        purchase_price = buy_price * quantity

    if holding_days is not None:
        holding_period_days = holding_days

    errors: list[str] = []
    warnings: list[str] = []

    if sale_price < 0:
        errors.append("Sale price cannot be negative")
    if purchase_price < 0:
        errors.append("Purchase price cannot be negative")
    if expenses_on_sale < 0:
        errors.append("Expenses on sale cannot be negative")

    if errors:
        return {
            "short_term_gains": 0.0,
            "long_term_gains": 0.0,
            "total_gains": 0.0,
            "tax_liability": 0.0,
            "asset_type": asset_type,
            "exemption_applied": 0.0,
            "taxable_gain": 0.0,
            "errors": errors,
            "warnings": warnings,
        }

    is_long_term = holding_period_days >= 365
    is_equity = asset_type in ("equity", "mutual_fund", "equity_mf")

    if is_equity:
        stcg_rate = 0.20
        ltcg_rate = 0.125
        threshold = LTCG_EQUITY_EXEMPTION
        indexation_required = False
    elif asset_type == "real_estate":
        stcg_rate = 0.20
        ltcg_rate = 0.20
        threshold = 0
        indexation_required = True
    elif asset_type in ("gold", "debentures"):
        stcg_rate = 0.30
        ltcg_rate = 0.20
        threshold = 0
        indexation_required = True
    elif asset_type == "crypto":
        stcg_rate = 0.30
        ltcg_rate = 0.30
        threshold = 0
        indexation_required = False
        warnings.append("Cryptocurrency gains taxed at flat 30% per Budget 2024")
    else:
        stcg_rate = 0.20
        ltcg_rate = 0.20
        threshold = 0
        indexation_required = False

    if indexation_required and inflation_index_purchase and inflation_index_sale:
        indexed_purchase = purchase_price * (inflation_index_sale / inflation_index_purchase)
        cost_inflation_adjusted = indexed_purchase + improvements
    else:
        cost_inflation_adjusted = purchase_price + improvements

    gross_gains = sale_price - cost_inflation_adjusted - expenses_on_sale
    gross_gains = max(0, gross_gains)

    exemption_applied = 0.0
    exemption_note = ""

    if is_long_term and is_equity:
        ltcg = gross_gains
        stcg = 0.0
        taxable_gain = max(0, ltcg - threshold)
        exemption_applied = min(ltcg, threshold)
        tax_liability = taxable_gain * ltcg_rate
        if exemption_applied > 0:
            exemption_note = (
                "₹1,00,000 annual LTCG exemption applied under Section 112A. "
                "This assumes no other LTCG in the financial year."
            )
    elif is_long_term:
        ltcg = gross_gains
        stcg = 0.0
        taxable_gain = ltcg
        tax_liability = taxable_gain * ltcg_rate
    else:
        stcg = gross_gains
        ltcg = 0.0
        taxable_gain = stcg
        tax_liability = stcg * stcg_rate

    if not is_long_term and is_equity:
        warnings.append("STCG on equity/MF taxed at 20% instead of slab rates per Budget 2024")

    if asset_type == "real_estate" and not (inflation_index_purchase and inflation_index_sale):
        warnings.append(
            "Real estate LTCG without indexation may result in higher tax. "
            "Consider providing CII for accurate calculation."
        )

    return {
        "short_term_gains": round(stcg, 2),
        "long_term_gains": round(ltcg, 2),
        "total_gains": round(gross_gains, 2),
        "gain_type": "LTCG" if is_long_term else "STCG",
        "is_long_term": is_long_term,
        "holding_period_days": holding_period_days,
        "tax_liability": round(tax_liability, 2),
        "asset_type": asset_type,
        "stcg_rate": stcg_rate * 100,
        "ltcg_rate": ltcg_rate * 100,
        "cost_inflation_adjusted": round(cost_inflation_adjusted, 2),
        "exemption_threshold": threshold if is_equity else 0,
        "exemption_applied": round(exemption_applied, 2),
        "taxable_gain": round(taxable_gain, 2),
        "exemption_note": exemption_note,
        "errors": errors,
        "warnings": warnings,
    }


def calculate_home_loan_savings(
    property_sale_price: float,
    property_purchase_price: float,
    loan_outstanding: float,
    holding_period_days: int,
) -> dict[str, Any]:
    """Calculate capital gains and tax savings from home sale with loan.

    Under Section 54/54F, if capital gains are reinvested in new property,
    tax can be deferred. This calculates the potential savings.
    """
    gains_result = calculate_capital_gains(
        sale_price=property_sale_price,
        purchase_price=property_purchase_price,
        asset_type="real_estate",
        holding_period_days=holding_period_days,
    )

    capital_gains = gains_result["total_gains"]
    tax_liability = gains_result["tax_liability"]

    reinvestment_threshold = capital_gains

    return {
        "capital_gains": capital_gains,
        "tax_liability": tax_liability,
        "reinvestment_required": reinvestment_threshold,
        "tax_savings_available": tax_liability if reinvestment_threshold > 0 else 0,
        "eligible_exemption": "Section 54 (individual)" if capital_gains > 0 else "N/A",
        "holding_period_met": holding_period_days >= 730,
        "note": "To claim exemption under Section 54, reinvest in new property within 2 years "
        "or construct within 3 years. Hold for 3 years for new property.",
    }
