"""PRAN (Permanent Retirement Account Number) validator for NPS."""

from __future__ import annotations

from typing import Any

PRAN_CATEGORIES = {
    "1": "Central Government",
    "2": "State Government",
    "3": "Corporate/Private",
    "4": "Atal Pension Yojana",
    "5": "NPS Lite",
}

DISCLAIMER = "Structural validation only. Does not verify with NPS Trust/NSDL."


def validate_pran(pran: str) -> dict[str, Any]:
    """Validate PRAN format.

    Args:
        pran: 12-digit PRAN

    Returns:
        Dict with validation and category.
    """
    cleaned = pran.strip().replace(" ", "").replace("-", "")

    if len(cleaned) != 12 or not cleaned.isdigit():
        return {"valid": False, "error": "PRAN must be 12 digits", "disclaimer": DISCLAIMER}

    first_digit = cleaned[0]
    category = PRAN_CATEGORIES.get(first_digit, "Unknown")

    return {
        "valid": True,
        "pran": cleaned,
        "subscriber_category": category,
        "note": "Structural validation only. Does not verify with NPS Trust/NSDL.",
        "disclaimer": DISCLAIMER,
    }
