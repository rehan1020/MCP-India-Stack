"""Indian mobile number validator with operator/circle detection."""

from __future__ import annotations

import re
from typing import Any

MOBILE_PREFIXES = {
    "9820": ("Jio", "Maharashtra"),
    "9821": ("Jio", "Gujarat"),
    "9822": ("Jio", "Karnataka"),
    "9823": ("Jio", "Delhi"),
    "9824": ("Jio", "Mumbai"),
    "9830": ("Jio", "West Bengal"),
    "9831": ("Jio", "Bihar"),
    "9832": ("Jio", "Orissa"),
    "9833": ("Jio", "North East"),
    "9834": ("Jio", "Assam"),
    "9835": ("Jio", "Punjab"),
    "9836": ("Jio", "Haryana"),
    "9837": ("Jio", "Rajasthan"),
    "9840": ("Airtel", "Tamil Nadu"),
    "9841": ("Airtel", "Karnataka"),
    "9842": ("Airtel", "Andhra Pradesh"),
    "9843": ("Airtel", "Telangana"),
    "9844": ("Airtel", "Kerala"),
    "9845": ("Airtel", "Delhi"),
    "9846": ("Airtel", "Mumbai"),
    "9847": ("Airtel", "Maharashtra"),
    "9848": ("Airtel", "Gujarat"),
    "9850": ("Vodafone", "Mumbai"),
    "9851": ("Vodafone", "Delhi"),
    "9852": ("Vodafone", "Gujarat"),
    "9853": ("Vodafone", "Maharashtra"),
    "9854": ("Vodafone", "Karnataka"),
    "9855": ("Vodafone", "Kerala"),
    "9856": ("Vodafone", "Punjab"),
    "9857": ("Vodafone", "Haryana"),
    "9858": ("Vodafone", "Bihar"),
    "9859": ("Vodafone", "Orissa"),
    "9860": ("BSNL", "Maharashtra"),
    "9861": ("BSNL", "Gujarat"),
    "9862": ("BSNL", "Karnataka"),
    "9863": ("BSNL", "Tamil Nadu"),
    "9864": ("BSNL", "Delhi"),
    "9865": ("BSNL", "West Bengal"),
    "9866": ("BSNL", "Punjab"),
    "9867": ("BSNL", "Rajasthan"),
    "9868": ("BSNL", "Madhya Pradesh"),
    "9869": ("BSNL", "Uttar Pradesh"),
}

DISCLAIMER = "MNP (Mobile Number Portability) may have changed the actual operator."


def _normalise_mobile(raw: str) -> str:
    """Normalise mobile number: strip non-digits, then remove country/STD prefix."""
    digits = re.sub(r"\D", "", raw)  # strip +, spaces, hyphens, brackets
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]  # strip country code 91
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]  # strip STD 0
    return digits


def validate_mobile_number(mobile: str) -> dict[str, Any]:
    """Validate Indian mobile number and detect operator/circle.

    Args:
        mobile: Mobile number with or without +91/0

    Returns:
        Dict with validation and operator info.
    """
    normalized = _normalise_mobile(mobile)

    if len(normalized) != 10 or not normalized.isdigit():
        return {
            "valid": False,
            "error": (
                f"Mobile number must be 10 digits after stripping country code;"
                f" got {len(normalized)}"
            ),
            "disclaimer": DISCLAIMER,
        }

    if normalized[0] not in "6789":
        return {
            "valid": False,
            "error": "Indian mobile numbers must start with 6, 7, 8, or 9",
            "disclaimer": DISCLAIMER,
        }

    prefix = normalized[:4]
    operator, circle = MOBILE_PREFIXES.get(prefix, ("Unknown", "Unknown"))

    return {
        "valid": True,
        "normalized": normalized,
        "formatted_e164": f"+91{normalized}",
        "prefix": prefix,
        "operator": operator,
        "telecom_circle": circle,
        "note": "MNP may have changed actual operator.",
        "disclaimer": DISCLAIMER,
    }
