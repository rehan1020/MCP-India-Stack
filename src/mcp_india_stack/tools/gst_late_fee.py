"""GST late fee calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "As per GST Council notifications up to 2024. Verify for any waivers."


def calculate_gst_late_fee(
    return_type: str,
    days_delayed: int,
    annual_turnover: float,
    has_nil_liability: bool = False,
) -> dict[str, Any]:
    """Calculate GST late filing penalty.

    Args:
        return_type: "GSTR1", "GSTR3B", or "GSTR9"
        days_delayed: Number of days delayed
        annual_turnover: Annual turnover for cap calculation
        has_nil_liability: True if nil return

    Returns:
        Dict with late fee breakdown.
    """
    errors = []
    if return_type not in ("GSTR1", "GSTR3B", "GSTR9"):
        errors.append("Invalid return_type")
    if days_delayed < 0:
        errors.append("days_delayed cannot be negative")

    if errors:
        return {"errors": errors, "disclaimer": DISCLAIMER}

    cap: float = 0.0

    if return_type == "GSTR9":
        daily_fee = 200
        cap_percent = 0.25
    else:
        # Nil return: ₹20/day (₹10 CGST + ₹10 SGST), not ₹25
        daily_fee = 20 if has_nil_liability else 50
        if annual_turnover <= 15000000:
            cap = 2000
        elif annual_turnover <= 50000000:
            cap = 5000
        else:
            cap = 10000

    computed_fee: float = daily_fee * days_delayed

    # Apply cap for ALL return types including GSTR9
    if return_type == "GSTR9":
        gstr9_cap = round(annual_turnover * cap_percent / 100, 2)
        computed_fee = min(computed_fee, gstr9_cap)
        cap = gstr9_cap
    else:
        computed_fee = min(computed_fee, cap)

    cgst_fee = computed_fee / 2
    sgst_fee = computed_fee / 2

    return {
        "return_type": return_type,
        "days_delayed": days_delayed,
        "daily_fee": daily_fee,
        "computed_fee_before_cap": daily_fee * days_delayed,
        "fee_cap": cap,
        "cgst_fee": round(cgst_fee, 2),
        "sgst_fee": round(sgst_fee, 2),
        "total_late_fee": computed_fee,
        "note": "Interest on tax liability is separate.",
        "disclaimer": DISCLAIMER,
    }
