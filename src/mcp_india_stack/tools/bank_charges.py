"""NEFT/RTGS/IMPS transaction charges calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Per RBI/NPCI guidelines. Actual bank charges may be lower."


def calculate_neft_rtgs_imps_charges(  # noqa: C901
    transfer_mode: str,
    amount: float,
    account_type: str = "savings",
    is_online: bool = True,
) -> dict[str, Any]:  # noqa: C901
    """Calculate transaction charges for NEFT/RTGS/IMPS.

    Args:
        transfer_mode: "NEFT", "RTGS", "IMPS", "UPI"
        amount: Transfer amount
        account_type: "savings" or "current"
        is_online: True if done via online banking

    Returns:
        Dict with charge breakdown.
    """
    errors = []
    if transfer_mode not in ("NEFT", "RTGS", "IMPS", "UPI"):
        errors.append("Invalid transfer_mode")
    if amount <= 0:
        errors.append("amount must be > 0")

    if errors:
        return {"errors": errors, "disclaimer": DISCLAIMER}

    base_charge = 0.0

    if transfer_mode == "NEFT":
        if is_online and account_type == "savings":
            base_charge = 0
        else:
            if amount <= 10000:
                base_charge = 2.50
            elif amount <= 100000:
                base_charge = 5
            elif amount <= 200000:
                base_charge = 15
            else:
                base_charge = 25

    elif transfer_mode == "RTGS":
        if amount < 200000:
            return {"errors": ["RTGS minimum is ₹2,00,000"], "disclaimer": DISCLAIMER}
        if is_online and account_type == "savings":
            base_charge = 0
        else:
            base_charge = 25 if amount <= 500000 else 50

    elif transfer_mode == "IMPS":
        if amount <= 100000:
            base_charge = 5 if amount > 1000 else 0
        elif amount <= 200000:
            base_charge = 15
        else:
            base_charge = 25

    elif transfer_mode == "UPI":
        base_charge = 0

    gst = round(base_charge * 0.18, 2)
    total = base_charge + gst

    return {
        "transfer_mode": transfer_mode,
        "amount": amount,
        "base_charge": round(base_charge, 2),
        "gst_18pct": gst,
        "total_charge": round(total, 2),
        "disclaimer": DISCLAIMER,
    }
