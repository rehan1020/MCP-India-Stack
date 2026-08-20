"""Capital gains calculator for Indian income tax."""

from __future__ import annotations

from typing import Any

LTCG_EQUITY_EXEMPTION = 125000  # ₹1,25,000 per year (Section 112A)

# LTCG holding period thresholds per Income Tax Act (in days)
LTCG_THRESHOLDS = {
    "equity": 365,  # 12 months
    "equity_mf": 365,
    "mutual_fund": 365,
    "real_estate": 730,  # 24 months
    "gold": 1095,  # 36 months
    "debentures": 1095,
    "crypto": 0,  # always flat 30% — no LTCG concept
}


def _get_ltcg_threshold(asset_type: str) -> int:
    """Return the LTCG holding period threshold for a given asset type."""
    return LTCG_THRESHOLDS.get(asset_type, 365)


def calculate_capital_gains(  # noqa: C901
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
    reinvestment_amount: float = 0.0,
) -> dict[str, Any]:  # noqa: C901
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
        reinvestment_amount: Amount reinvested in Section 54/54F eligible assets.

    Returns:
        Dict with gains, tax rates, exemption eligibility, and tax liability.
    """
    if buy_price is not None and sell_price is not None and quantity is not None:
        sale_price = sell_price * quantity
        purchase_price = buy_price * quantity
    elif quantity is not None and quantity > 1:
        sale_price = sale_price * quantity
        purchase_price = purchase_price * quantity

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

    # Use asset-type-specific LTCG threshold
    ltcg_threshold = _get_ltcg_threshold(asset_type)

    # Crypto has no LTCG concept — always taxed at flat 30%
    if asset_type == "crypto":
        is_long_term = False
    else:
        is_long_term = holding_period_days >= ltcg_threshold

    is_equity = asset_type in ("equity", "mutual_fund", "equity_mf")

    stcg_note = None

    if is_equity:
        stcg_rate = 0.20
        ltcg_rate = 0.125
        threshold = LTCG_EQUITY_EXEMPTION
        indexation_required = False
    elif asset_type == "real_estate":
        stcg_rate = None  # slab rate — can't compute without income
        ltcg_rate = 0.20
        threshold = 0
        indexation_required = True
        stcg_note = "STCG on real estate is added to income and taxed at applicable slab rate."
    elif asset_type in ("gold", "debentures"):
        stcg_rate = None  # slab rate
        ltcg_rate = 0.20
        threshold = 0
        indexation_required = True
        stcg_note = "STCG on gold/debentures is taxed at applicable income slab rate."
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
                "₹1,25,000 annual LTCG exemption applied under Section 112A. "
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
        if stcg_rate is not None:
            tax_liability = stcg * stcg_rate
        else:
            # Slab-rate assets: can't compute exact tax without full income
            # Use 30% as upper estimate with a warning
            tax_liability = stcg * 0.30
            warnings.append(stcg_note or "STCG is taxed at applicable income slab rate.")

    if not is_long_term and is_equity:
        warnings.append("STCG on equity/MF taxed at 20% instead of slab rates per Budget 2024")

    if asset_type == "real_estate" and not (inflation_index_purchase and inflation_index_sale):
        warnings.append(
            "Real estate LTCG without indexation may result in higher tax. "
            "Consider providing CII for accurate calculation."
        )

    section_54_exemption = 0.0
    section_54_taxable_gains = taxable_gain
    section_54f_exemption = 0.0
    section_54f_taxable_gains = taxable_gain
    section_54_note = None
    section_54f_note = None

    if reinvestment_amount > 0 and is_long_term:
        if asset_type == "real_estate":
            section_54_exemption = min(ltcg, reinvestment_amount)
            section_54_taxable_gains = taxable_gain - section_54_exemption
            section_54_note = (
                f"Section 54 exemption: ₹{section_54_exemption:,.0f}. "
                "Conditions: Purchase new property within 2 years or construct within 3 years."
            )
        elif asset_type != "real_estate":
            section_54f_exemption = (
                ltcg * (reinvestment_amount / sale_price) if sale_price > 0 else 0
            )
            section_54f_exemption = min(section_54f_exemption, ltcg)
            section_54f_taxable_gains = taxable_gain - section_54f_exemption
            section_54f_note = (
                f"Section 54F exemption: ₹{section_54f_exemption:,.0f}. "
                "Conditions: Invest full sale proceeds in residential property."
            )

    # Display-friendly STCG rate
    stcg_rate_display = stcg_rate * 100 if stcg_rate is not None else "slab_rate"

    result = {
        "short_term_gains": round(stcg, 2),
        "long_term_gains": round(ltcg, 2),
        "total_gains": round(gross_gains, 2),
        "gain_type": "LTCG" if is_long_term else "STCG",
        "is_long_term": is_long_term,
        "holding_period_days": holding_period_days,
        "ltcg_threshold_days": ltcg_threshold,
        "tax_liability": round(tax_liability, 2),
        "tax_amount": round(tax_liability, 2),
        "asset_type": asset_type,
        "stcg_rate": stcg_rate_display,
        "ltcg_rate": ltcg_rate * 100,
        "cost_inflation_adjusted": round(cost_inflation_adjusted, 2),
        "exemption_threshold": threshold if is_equity else 0,
        "exemption_applied": round(exemption_applied, 2),
        "taxable_gain": round(taxable_gain, 2),
        "exemption_note": exemption_note,
        "section_54_exemption_claimed": round(section_54_exemption, 2)
        if section_54_exemption > 0
        else 0,
        "section_54_taxable_gains": round(section_54_taxable_gains, 2),
        "section_54_note": section_54_note,
        "section_54f_exemption_claimed": round(section_54f_exemption, 2)
        if section_54f_exemption > 0
        else 0,
        "section_54f_taxable_gains": round(section_54f_taxable_gains, 2),
        "section_54f_note": section_54f_note,
        "reinvestment_amount": reinvestment_amount,
        "errors": errors,
        "warnings": warnings,
    }

    if stcg_note and not is_long_term:
        result["stcg_note"] = stcg_note

    return result


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
