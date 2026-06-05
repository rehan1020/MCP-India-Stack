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
    "194R": {
        "description": "Perquisite or benefit to resident",
        "rate": 0.10,
        "threshold": 20_000,
        "no_pan_rate": 0.20,
    },
    "194S": {
        "description": "Virtual digital assets/crypto transfer",
        "rate": 0.01,
        "threshold": 10_000,
        "no_pan_rate": 0.20,
    },
    "194M": {
        "description": "Contractor/Professional by individual without TAN",
        "rate": 0.05,
        "threshold": 5_000_000,
        "no_pan_rate": 0.20,
    },
}

DISCLAIMER = (
    "TDS rates are for FY2025-26 general reference. Actual rates may vary "
    "based on DTAA provisions, Form 15G/15H, and specific exemptions."
)


def calculate_tds(  # noqa: C901
    section: str,
    payment_amount: float,
    pan_available: bool,
    is_senior_citizen: bool = False,
    aggregate_payments_ytd: float = 0.0,
    payee_type: str = "individual_huf",
) -> dict[str, Any]:  # noqa: C901
    """Calculate TDS for a given section and payment amount.

    Args:
        section: TDS section key from TDS_SECTIONS table.
        payment_amount: Gross payment amount in rupees.
        pan_available: Whether payee has provided PAN.
        is_senior_citizen: For 194A bank interest, applies ₹50K threshold.
        aggregate_payments_ytd: Prior payments to same payee under this section in current FY.
        payee_type: "individual_huf" or "other" - affects 194C rate.

    Returns:
        Dict with TDS calculation results.
    """
    try:
        errors: list[str] = []

        if section == "194C":
            if payee_type in ("other", "company"):
                section = "194C_company"
            else:
                section = "194C_individual"
        elif section == "194J":
            section = "194J_professional"
        elif section == "194A":
            section = "194A_bank"

        if section not in TDS_SECTIONS:
            errors.append(
                f"Unknown TDS section '{section}'. Valid sections: {sorted(TDS_SECTIONS.keys())}"
            )

        if payment_amount is None or not isinstance(payment_amount, (int, float)):
            errors.append("payment_amount is required and must be a number")
        elif payment_amount < 0:
            errors.append("payment_amount cannot be negative")

        if payee_type not in ("individual_huf", "other", "company"):
            errors.append("payee_type must be 'individual_huf', 'company', or 'other'")

        if errors:
            return {
                "financial_year": "2025-26",
                "section": section,
                "description": "",
                "payment_amount": payment_amount if isinstance(payment_amount, (int, float)) else 0,
                "threshold_single": 0,
                "threshold_aggregate": 0,
                "aggregate_threshold_crossed": False,
                "aggregate_total_after_payment": 0,
                "tds_applicable": False,
                "rate_applied": 0,
                "tds_amount": 0,
                "net_payment": 0,
                "pan_available": pan_available,
                "payee_type_applied": payee_type,
                "no_pan_surcharge": 0,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        section_info = TDS_SECTIONS[section]
        description = section_info["description"]

        # Determine threshold
        threshold_single = section_info["threshold"]
        threshold_aggregate = section_info.get("annual_threshold", 0)

        if section == "194A_bank" and is_senior_citizen:
            threshold_single = section_info.get("senior_threshold", threshold_single)

        # Adjust rate for 194C based on payee type
        rate = section_info["rate"]
        if section == "194C_individual":
            rate = 0.01
        elif section == "194C_company":
            rate = 0.02
        elif section == "194C" and payee_type == "other":
            rate = 0.02
        elif section == "194C" and payee_type == "individual_huf":
            rate = 0.01

        # Check aggregate threshold for sections that have it
        aggregate_total_after = aggregate_payments_ytd + payment_amount
        aggregate_threshold_crossed = False
        if threshold_aggregate > 0:
            aggregate_threshold_crossed = aggregate_total_after > threshold_aggregate

        # Check if TDS is applicable (either single threshold or aggregate threshold)
        single_threshold_crossed = payment_amount >= threshold_single
        tds_applicable = single_threshold_crossed or aggregate_threshold_crossed

        if not tds_applicable:
            return {
                "financial_year": "2025-26",
                "section": section,
                "description": description,
                "payment_amount": payment_amount,
                "threshold_single": threshold_single,
                "threshold_aggregate": threshold_aggregate,
                "aggregate_threshold_crossed": aggregate_threshold_crossed,
                "aggregate_total_after_payment": aggregate_total_after,
                "tds_applicable": False,
                "rate_applied": 0,
                "tds_amount": 0,
                "net_payment": payment_amount,
                "pan_available": pan_available,
                "payee_type_applied": payee_type,
                "no_pan_surcharge": 0,
                "errors": [],
                "disclaimer": DISCLAIMER,
            }

        # Calculate TDS
        if pan_available:
            tds_amount = round(payment_amount * rate, 2)
            no_pan_surcharge = 0.0
            rate_applied = rate
        else:
            no_pan_rate = section_info["no_pan_rate"]
            tds_amount = round(payment_amount * no_pan_rate, 2)
            no_pan_surcharge = round(payment_amount * (no_pan_rate - rate), 2)
            rate_applied = no_pan_rate

        net_payment = round(payment_amount - tds_amount, 2)

        return {
            "financial_year": "2025-26",
            "section": section,
            "description": description,
            "payment_amount": payment_amount,
            "threshold_single": threshold_single,
            "threshold_aggregate": threshold_aggregate,
            "aggregate_threshold_crossed": aggregate_threshold_crossed,
            "aggregate_total_after_payment": aggregate_total_after,
            "tds_applicable": True,
            "rate_applied": rate_applied,
            "tds_amount": tds_amount,
            "net_payment": net_payment,
            "pan_available": pan_available,
            "payee_type_applied": payee_type,
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
            "threshold_single": 0,
            "threshold_aggregate": 0,
            "aggregate_threshold_crossed": False,
            "aggregate_total_after_payment": 0,
            "tds_applicable": False,
            "rate_applied": 0,
            "tds_amount": 0,
            "net_payment": 0,
            "pan_available": pan_available if isinstance(pan_available, bool) else False,
            "payee_type_applied": payee_type if isinstance(payee_type, str) else "individual_huf",
            "no_pan_surcharge": 0,
            "errors": [f"TDS calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
