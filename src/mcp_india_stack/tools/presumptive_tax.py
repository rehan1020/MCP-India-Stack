"""Presumptive tax calculator (Sections 44AD, 44ADA).

Section 44AD — business:
  ₹3 crore limit (>= 95% digital receipts/payments)
  ₹2 crore limit (general / cash-heavy)

Section 44ADA — professionals (doctors, lawyers, architects, etc.):
  ₹75 lakhs limit (>= 95% digital, raised from ₹50L by Finance Act 2023)
  ₹50 lakhs limit (< 95% digital)
"""

from __future__ import annotations

from typing import Any

# --- Eligibility thresholds ---
LIMIT_44AD_DIGITAL = 3_00_00_000  # ₹3 crore (>95% digital receipts/payments)
LIMIT_44AD_CASH = 2_00_00_000  # ₹2 crore (general / cash-heavy)
LIMIT_44ADA_DIGITAL = 75_00_000  # ₹75 lakhs (>= 95% digital)
LIMIT_44ADA_CASH = 50_00_000  # ₹50 lakhs (< 95% digital)

DISCLAIMER = "Eligibility conditions apply. Consult a CA if you have international transactions."

# --- Full tax slab tables ---
NEW_REGIME_SLABS = [
    (4_00_000, 0.00),
    (8_00_000, 0.05),
    (12_00_000, 0.10),
    (16_00_000, 0.15),
    (20_00_000, 0.20),
    (24_00_000, 0.25),
    (float("inf"), 0.30),
]

OLD_REGIME_SLABS = [
    (2_50_000, 0.00),
    (5_00_000, 0.05),
    (10_00_000, 0.20),
    (float("inf"), 0.30),
]


def _compute_slab_tax(taxable: float, slabs: list[tuple[float, float]]) -> float:
    """Compute tax using a slab table."""
    tax = 0.0
    prev = 0.0
    for limit, rate in slabs:
        if taxable <= prev:
            break
        slab_income = min(taxable, limit) - prev
        tax += slab_income * rate
        prev = limit
    return round(tax, 2)


def calculate_presumptive_tax(
    scheme: str,
    gross_receipts: float,
    digital_receipt_percent: float = 100.0,
    regime: str = "new",
    age: int = 35,
    deductions_80c: float = 0,
) -> dict[str, Any]:
    """Calculate tax under presumptive scheme.

    Args:
        scheme: "44AD" or "44ADA"
        gross_receipts: Total gross receipts
        digital_receipt_percent: % of receipts via digital mode
        regime: "new" or "old"
        age: Assessee age
        deductions_80c: Section 80C deductions (old regime)

    Returns:
        Dict with presumptive income and tax.
    """
    errors = []
    if scheme not in ("44AD", "44ADA"):
        errors.append("Invalid scheme")
    if gross_receipts <= 0:
        errors.append("gross_receipts must be > 0")

    if errors:
        return {"errors": errors, "disclaimer": DISCLAIMER}

    if scheme == "44AD":
        threshold = LIMIT_44AD_DIGITAL if digital_receipt_percent >= 95 else LIMIT_44AD_CASH
        if gross_receipts > threshold:
            limit_str = (
                f"₹{threshold / 1e7:.1f} crore"
                if threshold >= 1_00_00_000
                else f"₹{threshold / 1e5:.0f} lakhs"
            )
            return {
                "errors": [
                    f"Gross receipts ₹{gross_receipts:,.0f} exceed the Section 44AD limit of "
                    f"{limit_str} "
                    f"({'digital' if digital_receipt_percent >= 95 else 'cash'} threshold). "
                    f"Maintain books of accounts under normal provisions."
                ],
                "disclaimer": DISCLAIMER,
            }
        presumptive_rate = 0.06 * (digital_receipt_percent / 100) + 0.08 * (
            (100 - digital_receipt_percent) / 100
        )
        presumptive_income = gross_receipts * presumptive_rate
    else:  # 44ADA
        threshold = LIMIT_44ADA_DIGITAL if digital_receipt_percent >= 95 else LIMIT_44ADA_CASH
        if gross_receipts > threshold:
            return {
                "errors": [
                    f"Gross receipts ₹{gross_receipts:,.0f} exceed the Section 44ADA limit of "
                    f"₹{threshold / 1e5:.0f} lakhs. Maintain books under normal provisions."
                ],
                "disclaimer": DISCLAIMER,
            }
        presumptive_income = gross_receipts * 0.50

    # Tax computation using full slab tables
    if regime == "old":
        taxable = max(0, presumptive_income - min(deductions_80c, 150000) - 50000)
        tax = _compute_slab_tax(taxable, OLD_REGIME_SLABS)
        # 87A rebate: if taxable <= ₹5L, tax = 0
        if taxable <= 5_00_000:
            tax = 0
    else:  # new regime
        taxable = max(0, presumptive_income - 75000)
        tax = _compute_slab_tax(taxable, NEW_REGIME_SLABS)
        # 87A rebate: if taxable <= ₹12L, tax = 0
        if taxable <= 12_00_000:
            tax = 0

    cess = round(tax * 0.04, 2)
    tax_after_cess = round(tax + cess, 2)
    effective_rate = (tax_after_cess / gross_receipts * 100) if gross_receipts > 0 else 0

    return {
        "scheme": scheme,
        "gross_receipts": gross_receipts,
        "presumptive_income": round(presumptive_income, 2),
        "presumptive_rate": f"{presumptive_rate * 100}%" if scheme == "44AD" else "50%",
        "taxable_income": round(taxable, 2),
        "tax_before_cess": round(tax, 2),
        "cess": cess,
        "tax_after_cess": tax_after_cess,
        "total_tax_payable": tax_after_cess,
        "effective_rate_on_receipts": round(effective_rate, 2),
        "advance_tax_note": "Entire advance tax can be paid in one installment by March 15.",
        "disclaimer": DISCLAIMER,
    }
