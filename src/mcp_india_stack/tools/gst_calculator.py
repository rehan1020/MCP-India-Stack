"""GST calculator — CGST/SGST/IGST breakdown with cess support."""

from __future__ import annotations

from typing import Any

VALID_GST_RATES = [0, 0.1, 0.25, 1.5, 3, 5, 12, 18, 28]

CESS_RATES: dict[str, float] = {
    "luxury_cars_above_4m": 0.20,
    "small_petrol_cars": 0.01,
    "small_diesel_cars": 0.03,
    "aerated_drinks": 0.12,
    "tobacco_cigarettes": 0.05,
    "pan_masala": 0.60,
    "default": 0.00,
}

HSN_RATE_MAP: dict[str, int] = {
    "99": 18,
    "9954": 18,  # Construction services
    "9963": 18,  # Accommodation
    "9972": 18,  # Real estate
    "9983": 18,  # Professional services
    "9984": 18,  # Telecom
    "9985": 18,  # Support services
    "9993": 0,  # Health, education
}

DISCLAIMER = (
    "GST rates are for general reference. Actual rates may vary by "
    "specific HSN/SAC classification and applicable government notifications."
)


from mcp_india_stack.utils.loader import load_hsn_index


def _lookup_hsn_rate(hsn_code: str) -> tuple[float | None, list[str]]:
    """Look up GST rate from HSN code with fallback logic."""
    searched_prefixes = []
    hsn = hsn_code.strip().upper()
    hsn_index = load_hsn_index()

    for length in [8, 6, 4, 2]:
        if len(hsn) >= length:
            prefix = hsn[:length]
            searched_prefixes.append(prefix)

            # 1. Fallback to hardcoded map (more reliable for services)
            if prefix in HSN_RATE_MAP:
                return float(HSN_RATE_MAP[prefix]), searched_prefixes

            # 2. Check full dataset
            if prefix in hsn_index and hsn_index[prefix]:
                # get IGST_Rate from the first matching row
                try:
                    return float(hsn_index[prefix][0].get("IGST_Rate", 0)), searched_prefixes
                except (ValueError, TypeError):
                    pass

    return None, searched_prefixes


def calculate_gst(  # noqa: C901
    amount: float,
    gst_rate: float | None = None,
    transaction_type: str = "intra_state",
    amount_includes_gst: bool = False,
    cess_category: str = "default",
    hsn_code: str | None = None,
) -> dict[str, Any]:  # noqa: C901
    """Calculate GST breakdown for a given amount and rate.

    Args:
        amount: Base amount in rupees (or GST-inclusive amount if flagged).
        gst_rate: GST rate as a percentage (optional if hsn_code provided).
        transaction_type: "intra_state" (CGST+SGST) or "inter_state" (IGST).
        amount_includes_gst: If True, back-calculate base from inclusive amount.
        cess_category: For 28% items, specify cess category key.
        hsn_code: Optional HSN/SAC code to look up rate automatically.

    Returns:
        Dict with full GST breakdown.
    """
    try:
        errors: list[str] = []
        rate_source = "explicit"
        hsn_used = None

        if hsn_code:
            rate, searched = _lookup_hsn_rate(hsn_code)
            if rate is not None:
                gst_rate = rate
                hsn_used = hsn_code
                rate_source = "hsn_lookup"
            else:
                errors.append(f"HSN code '{hsn_code}' not found. Searched prefixes: {searched}")

        if amount is None or not isinstance(amount, (int, float)):
            return {
                "base_amount": 0,
                "gst_rate": 0,
                "transaction_type": "",
                "cgst_rate": 0,
                "sgst_rate": 0,
                "igst_rate": 0,
                "cgst_amount": 0,
                "sgst_amount": 0,
                "igst_amount": 0,
                "cess_rate": 0,
                "cess_amount": 0,
                "total_gst": 0,
                "total_amount": 0,
                "errors": ["Amount is required and must be a number"],
                "disclaimer": DISCLAIMER,
            }

        if amount < 0:
            errors.append("Amount cannot be negative")

        if gst_rate is None:
            errors.append("gst_rate is required if hsn_code is not provided")
        elif gst_rate not in VALID_GST_RATES:
            errors.append(f"Invalid GST rate {gst_rate}%. Valid rates: {VALID_GST_RATES}")

        if transaction_type not in ("intra_state", "inter_state"):
            errors.append("transaction_type must be 'intra_state' or 'inter_state'")

        if cess_category not in CESS_RATES:
            errors.append(
                f"Unknown cess_category '{cess_category}'. Valid: {list(CESS_RATES.keys())}"
            )

        if errors:
            return {
                "base_amount": 0,
                "gst_rate": gst_rate if gst_rate else 0,
                "transaction_type": transaction_type,
                "cgst_rate": 0,
                "sgst_rate": 0,
                "igst_rate": 0,
                "cgst_amount": 0,
                "sgst_amount": 0,
                "igst_amount": 0,
                "cess_rate": 0,
                "cess_amount": 0,
                "total_gst": 0,
                "total_amount": 0,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        assert gst_rate is not None  # ensured above — None would have appended errors and returned
        rate_fraction = gst_rate / 100
        cess_rate = CESS_RATES.get(cess_category, 0.0)

        if amount_includes_gst:
            base_amount = round(amount / (1 + rate_fraction + cess_rate), 2)
        else:
            base_amount = round(amount, 2)

        if transaction_type == "inter_state":
            igst_rate = gst_rate
            cgst_rate = 0.0
            sgst_rate = 0.0
            igst_amount = round(base_amount * rate_fraction, 2)
            cgst_amount = 0.0
            sgst_amount = 0.0
        else:
            igst_rate = 0.0
            cgst_rate = gst_rate / 2
            sgst_rate = gst_rate / 2
            cgst_amount = round(base_amount * (rate_fraction / 2), 2)
            sgst_amount = round(base_amount * (rate_fraction / 2), 2)
            igst_amount = 0.0

        cess_amount = round(base_amount * cess_rate, 2)
        total_gst = round(cgst_amount + sgst_amount + igst_amount, 2)
        total_amount = round(base_amount + total_gst + cess_amount, 2)

        result: dict[str, Any] = {
            "base_amount": base_amount,
            "gst_rate": gst_rate,
            "transaction_type": transaction_type,
            "cgst_rate": cgst_rate,
            "sgst_rate": sgst_rate,
            "igst_rate": igst_rate,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "cgst": cgst_amount,
            "sgst": sgst_amount,
            "igst": igst_amount,
            "cess_rate": cess_rate * 100,
            "cess_amount": cess_amount,
            "total_gst": total_gst,
            "total_amount": total_amount,
            "total_with_gst": total_amount,
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

        if hsn_code and hsn_used:
            result["hsn_code_used"] = hsn_code
            result["rate_source"] = rate_source
            result["note"] = (
                "Rate derived from HSN chapter. Verify exact rate for your specific "
                "product/service with the GST rate schedule."
            )

        return result

    except Exception as exc:
        return {
            "base_amount": 0,
            "gst_rate": 0,
            "transaction_type": "",
            "cgst_rate": 0,
            "sgst_rate": 0,
            "igst_rate": 0,
            "cgst_amount": 0,
            "sgst_amount": 0,
            "igst_amount": 0,
            "cess_rate": 0,
            "cess_amount": 0,
            "total_gst": 0,
            "total_amount": 0,
            "errors": [f"GST calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
