"""Indian passport number format validation."""

from __future__ import annotations

import re

PASSPORT_RE = re.compile(r"^[A-Z][0-9]{7}$")

DISCLAIMER = "Format validation only. Cannot verify passport validity or status."


def validate_passport(passport_number: str) -> dict[str, object]:
    """Validate an Indian passport number format.

    Format: 1 uppercase letter (series) + 7 digits (sequential number) = 8 characters.
    No publicly available checksum — format validation only.

    Args:
        passport_number: Indian passport number string.

    Returns:
        Dict with validation results.
    """
    try:
        if passport_number is None:
            return {
                "valid": False,
                "passport_number": "",
                "series_letter": "",
                "serial": "",
                "errors": ["Passport number is required"],
                "disclaimer": DISCLAIMER,
            }

        cleaned = str(passport_number).strip().upper()
        errors: list[str] = []

        if not cleaned:
            return {
                "valid": False,
                "passport_number": "",
                "series_letter": "",
                "serial": "",
                "errors": ["Passport number cannot be empty"],
                "disclaimer": DISCLAIMER,
            }

        if len(cleaned) != 8:
            errors.append(
                f"Indian passport number must be exactly 8 characters, got {len(cleaned)}"
            )
            return {
                "valid": False,
                "passport_number": cleaned,
                "series_letter": "",
                "serial": "",
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        if not PASSPORT_RE.match(cleaned):
            errors.append("Passport number must be 1 uppercase letter followed by 7 digits")
            return {
                "valid": False,
                "passport_number": cleaned,
                "series_letter": "",
                "serial": "",
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        return {
            "valid": True,
            "passport_number": cleaned,
            "series_letter": cleaned[0],
            "serial": cleaned[1:],
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "valid": False,
            "passport_number": str(passport_number) if passport_number else "",
            "series_letter": "",
            "serial": "",
            "errors": [f"Passport validation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
