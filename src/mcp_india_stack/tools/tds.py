"""TDS (Tax Deducted at Source) calculator for FY2025-26."""

from __future__ import annotations

from typing import Any

TDS_SECTIONS: dict[str, dict[str, Any]] = {
    "194C_individual": {
        "description": "Payment to contractor - Individual/HUF",
        "rate": 0.01,
        "threshold": 30_000,
        "annual_threshold": 100_000,
        "no_pan_rate": 0.20,
    },
    "194C_company": {
        "description": "Payment to contractor - Company",
        "rate": 0.02,
        "threshold": 30_000,
        "annual_threshold": 100_000,
        "no_pan_rate": 0.20,
    },
    "194J_professional": {
        "description": "Professional fees",
        "rate": 0.10,
        "threshold": 30_000,
        "no_pan_rate": 0.20,
    },
    "194J_technical": {
        "description": "Technical service fees",
        "rate": 0.02,
        "threshold": 30_000,
        "no_pan_rate": 0.20,
    },
    "194A_bank": {
        "description": "Interest from bank/post office",
        "rate": 0.10,
        "threshold": 40_000,
        "senior_threshold": 50_000,
        "no_pan_rate": 0.20,
    },
    "194A_other": {
        "description": "Interest from other sources",
        "rate": 0.10,
        "threshold": 5_000,
        "no_pan_rate": 0.20,
    },
    "194H": {
        "description": "Commission or brokerage",
        "rate": 0.05,
        "threshold": 15_000,
        "no_pan_rate": 0.20,
    },
    "194I_land": {
        "description": "Rent - Land, building, furniture",
        "rate": 0.10,
        "threshold": 240_000,
        "no_pan_rate": 0.20,
    },
    "194I_plant": {
        "description": "Rent - Plant and machinery",
        "rate": 0.02,
        "threshold": 240_000,
        "no_pan_rate": 0.20,
    },
    "194Q": {
        "description": "Purchase of goods",
        "rate": 0.001,
        "threshold": 5_000_000,
        "no_pan_rate": 0.05,
    },
    "194B": {
        "description": "Winnings from lottery/crossword",
        "rate": 0.30,
        "threshold": 10_000,
        "no_pan_rate": 0.30,
    },
    "194D": {
        "description": "Insurance commission",
        "rate": 0.05,
        "threshold": 15_000,
        "no_pan_rate": 0.20,
    },
}

DISCLAIMER = (
    "TDS rates are for FY2025-26 general reference. Actual rates may vary "
    "based on DTAA provisions, Form 15G/15H, and specific exemptions."
)


def calculate_tds(
    section: str,
    payment_amount: float,
    pan_available: bool,
    is_senior_citizen: bool = False,
) -> dict[str, Any]:
    """Calculate TDS for a given section and payment amount.

    Args:
        section: TDS section key from TDS_SECTIONS table.
        payment_amount: Gross payment amount in rupees.
        pan_available: Whether payee has provided PAN.
        is_senior_citizen: For 194A bank interest, applies ₹50K threshold.

    Returns:
        Dict with TDS calculation results.
    """
    try:
        errors: list[str] = []

        if section not in TDS_SECTIONS:
            errors.append(
                f"Unknown TDS section '{section}'. Valid sections: {sorted(TDS_SECTIONS.keys())}"
            )

        if payment_amount is None or not isinstance(payment_amount, (int, float)):
            errors.append("payment_amount is required and must be a number")
        elif payment_amount < 0:
            errors.append("payment_amount cannot be negative")

        if errors:
            return {
                "financial_year": "2025-26",
                "section": section,
                "description": "",
                "payment_amount": payment_amount if isinstance(payment_amount, (int, float)) else 0,
                "threshold": 0,
                "tds_applicable": False,
                "rate_applied": 0,
                "tds_amount": 0,
                "net_payment": 0,
                "pan_available": pan_available,
                "no_pan_surcharge": 0,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        section_info = TDS_SECTIONS[section]
        description = section_info["description"]

        # Determine threshold
        threshold = section_info["threshold"]
        if section == "194A_bank" and is_senior_citizen:
            threshold = section_info.get("senior_threshold", threshold)

        # Check if TDS is applicable
        tds_applicable = payment_amount >= threshold

        if not tds_applicable:
            return {
                "financial_year": "2025-26",
                "section": section,
                "description": description,
                "payment_amount": payment_amount,
                "threshold": threshold,
                "tds_applicable": False,
                "rate_applied": 0,
                "tds_amount": 0,
                "net_payment": payment_amount,
                "pan_available": pan_available,
                "no_pan_surcharge": 0,
                "errors": [],
                "disclaimer": DISCLAIMER,
            }

        # Calculate TDS
        if pan_available:
            rate = section_info["rate"]
            tds_amount = round(payment_amount * rate, 2)
            no_pan_surcharge = 0.0
        else:
            no_pan_rate = section_info["no_pan_rate"]
            normal_rate = section_info["rate"]
            tds_amount = round(payment_amount * no_pan_rate, 2)
            no_pan_surcharge = round(payment_amount * (no_pan_rate - normal_rate), 2)
            rate = no_pan_rate

        net_payment = round(payment_amount - tds_amount, 2)

        return {
            "financial_year": "2025-26",
            "section": section,
            "description": description,
            "payment_amount": payment_amount,
            "threshold": threshold,
            "tds_applicable": True,
            "rate_applied": rate,
            "tds_amount": tds_amount,
            "net_payment": net_payment,
            "pan_available": pan_available,
            "no_pan_surcharge": no_pan_surcharge,
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "financial_year": "2025-26",
            "section": section if isinstance(section, str) else "",
            "description": "",
            "payment_amount": payment_amount if isinstance(payment_amount, (int, float)) else 0,
            "threshold": 0,
            "tds_applicable": False,
            "rate_applied": 0,
            "tds_amount": 0,
            "net_payment": 0,
            "pan_available": pan_available if isinstance(pan_available, bool) else False,
            "no_pan_surcharge": 0,
            "errors": [f"TDS calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
