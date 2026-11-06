"""NEFT/RTGS/IMPS transaction charges calculator."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.rules_metadata import (
    attach_rule_metadata,
    validate_financial_year,
)

DISCLAIMER = "Per RBI/NPCI guidelines. Actual bank charges may be lower."


def calculate_neft_rtgs_imps_charges(  # noqa: C901
    transfer_mode: str,
    amount: float,
    account_type: str = "savings",
    is_online: bool = True,
    financial_year: str = "2025-26",
) -> dict[str, Any]:  # noqa: C901
    """Calculate transaction charges for NEFT/RTGS/IMPS.

    Args:
        transfer_mode: "NEFT", "RTGS", "IMPS", "UPI"
        amount: Transfer amount
        account_type: "savings" or "current"
        is_online: True if done via online banking
        financial_year: Financial year (defaults to "2025-26")

    Returns:
        Dict with charge breakdown.
    """
    is_valid_fy, err_resp = validate_financial_year("neft_rtgs_imps_charges", financial_year)
    if not is_valid_fy:
        assert err_resp is not None
        return err_resp

    errors = []
    if transfer_mode not in ("NEFT", "RTGS", "IMPS", "UPI"):
        errors.append("Invalid transfer_mode")
    if amount <= 0:
        errors.append("amount must be > 0")

    if errors:
        return attach_rule_metadata(
            {"errors": errors, "disclaimer": DISCLAIMER},
            "neft_rtgs_imps_charges",
            financial_year,
        )

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
            return attach_rule_metadata(
                {"errors": ["RTGS minimum is ₹2,00,000"], "disclaimer": DISCLAIMER},
                "neft_rtgs_imps_charges",
                financial_year,
            )
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

    res = {
        "transfer_mode": transfer_mode,
        "amount": amount,
        "base_charge": round(base_charge, 2),
        "gst_18pct": gst,
        "total_charge": round(total, 2),
        "disclaimer": DISCLAIMER,
    }
    return attach_rule_metadata(res, "neft_rtgs_imps_charges", financial_year)
