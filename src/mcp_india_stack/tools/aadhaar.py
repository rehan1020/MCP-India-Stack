"""Aadhaar number validation with Verhoeff checksum."""

from __future__ import annotations

import re

# --- Verhoeff lookup tables ---

d = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

p = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

inv = [0, 4, 3, 2, 1, 9, 8, 7, 6, 5]

DISCLAIMER = (
    "This tool validates format and checksum only. "
    "It is not connected to UIDAI and cannot verify identity."
)


def _verhoeff_checksum(number: str) -> bool:
    """Validate a number string using the Verhoeff algorithm.

    Args:
        number: String of digits to validate.

    Returns:
        True if checksum is valid (c == 0 after processing all digits).
    """
    c = 0
    digits = list(reversed(number))
    for i, digit_char in enumerate(digits):
        c = d[c][p[i % 8][int(digit_char)]]
    return c == 0


def validate_aadhaar(aadhaar: str) -> dict[str, object]:
    """Validate an Indian Aadhaar number (12-digit with Verhoeff checksum).

    Args:
        aadhaar: Aadhaar number string, may include spaces or hyphens.

    Returns:
        Dict with validation results including checksum status.
    """
    try:
        if aadhaar is None:
            return {
                "valid": False,
                "aadhaar": "",
                "formatted": "",
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": ["Aadhaar number is required"],
                "disclaimer": DISCLAIMER,
            }

        # Strip whitespace, spaces, and hyphens
        cleaned = re.sub(r"[\s\-]", "", str(aadhaar).strip())
        errors: list[str] = []
        warnings: list[str] = []

        # Check numeric
        if not cleaned.isdigit():
            return {
                "valid": False,
                "aadhaar": cleaned,
                "formatted": "",
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": ["Aadhaar number must contain only digits"],
                "disclaimer": DISCLAIMER,
            }

        # Check length
        if len(cleaned) != 12:
            return {
                "valid": False,
                "aadhaar": cleaned,
                "formatted": "",
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": [
                    f"Aadhaar number must be exactly 12 digits, got {len(cleaned)}"
                ],
                "disclaimer": DISCLAIMER,
            }

        # Check first digit
        first_digit_valid = cleaned[0] not in ("0", "1")
        if not first_digit_valid:
            errors.append(
                "Aadhaar numbers cannot start with 0 or 1 "
                "(UIDAI does not issue such numbers)"
            )

        # Verhoeff checksum
        checksum_valid = _verhoeff_checksum(cleaned)
        if not checksum_valid:
            errors.append("Verhoeff checksum validation failed")

        # Warn on all-same digits
        if len(set(cleaned)) == 1:
            warnings.append(
                "All digits are identical — this is unlikely to be a real Aadhaar number"
            )

        formatted = f"{cleaned[:4]} {cleaned[4:8]} {cleaned[8:12]}"
        valid = first_digit_valid and checksum_valid

        result: dict[str, object] = {
            "valid": valid,
            "aadhaar": cleaned,
            "formatted": formatted,
            "checksum_valid": checksum_valid,
            "first_digit_valid": first_digit_valid,
            "errors": errors,
            "disclaimer": DISCLAIMER,
        }
        if warnings:
            result["warnings"] = warnings
        return result

    except Exception as exc:
        return {
            "valid": False,
            "aadhaar": str(aadhaar) if aadhaar else "",
            "formatted": "",
            "checksum_valid": False,
            "first_digit_valid": False,
            "errors": [f"Aadhaar validation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
