"""Aadhaar number validation with Verhoeff checksum."""

from __future__ import annotations

import re

from mcp_india_stack.authenticity.rules import create_aadhaar_authenticity
from mcp_india_stack.logging_filter import mask_aadhaar_text

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
    "It is not connected to UIDAI and cannot verify identity. "
    "In compliance with DPDP Act 2023, raw Aadhaar numbers are never stored or logged."
)


def _mask_aadhaar(aadhaar: str, show_last: int = 4) -> str:
    """Mask Aadhaar number, showing only the last specified digits.

    Args:
        aadhaar: Full Aadhaar number string
        show_last: Number of last digits to show (default 4)

    Returns:
        Masked string like "XXXX XXXX 7261"
    """
    clean = re.sub(r"[\s\-]", "", str(aadhaar).strip())
    if len(clean) <= show_last:
        return "X" * len(clean)
    if len(clean) == 12:
        return f"XXXX XXXX {clean[-show_last:]}"
    return "X" * (len(clean) - show_last) + clean[-show_last:]


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

    UIDAI & DPDP Compliance:
    Validates structural format and Verhoeff checksum only. Not connected to UIDAI.
    In compliance with the Digital Personal Data Protection Act, 2023 (DPDP Act)
    and UIDAI guidelines, raw Aadhaar numbers are never stored, logged, or exposed in output.

    Args:
        aadhaar: Aadhaar number string, may include spaces or hyphens.

    Returns:
        Dict with validation results including checksum status.
        Never exposes the raw or full Aadhaar number — only a masked form.
    """
    try:
        if aadhaar is None:
            return {
                "valid": False,
                "masked": "",
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": ["Aadhaar number is required"],
                "disclaimer": DISCLAIMER,
                "authenticity": create_aadhaar_authenticity(
                    aadhaar="",
                    valid=False,
                    checksum_valid=False,
                    first_digit_valid=False,
                ),
            }

        # Strip whitespace, spaces, and hyphens
        cleaned = re.sub(r"[\s\-]", "", str(aadhaar).strip())
        errors: list[str] = []
        warnings: list[str] = []

        # Check numeric
        if not cleaned.isdigit():
            return {
                "valid": False,
                "masked": _mask_aadhaar(cleaned) if cleaned else "",
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": ["Aadhaar number must contain only digits"],
                "disclaimer": DISCLAIMER,
                "authenticity": create_aadhaar_authenticity(
                    aadhaar=cleaned,
                    valid=False,
                    checksum_valid=False,
                    first_digit_valid=False,
                ),
            }

        # Check length
        if len(cleaned) != 12:
            return {
                "valid": False,
                "masked": _mask_aadhaar(cleaned),
                "checksum_valid": False,
                "first_digit_valid": False,
                "errors": [f"Aadhaar number must be exactly 12 digits, got {len(cleaned)}"],
                "disclaimer": DISCLAIMER,
                "authenticity": create_aadhaar_authenticity(
                    aadhaar=cleaned,
                    valid=False,
                    checksum_valid=False,
                    first_digit_valid=False,
                ),
            }

        # Check first digit
        first_digit_valid = cleaned[0] not in ("0", "1")
        if not first_digit_valid:
            errors.append(
                "Aadhaar numbers cannot start with 0 or 1 (UIDAI does not issue such numbers)"
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

        masked = _mask_aadhaar(cleaned)
        valid = first_digit_valid and checksum_valid
        auth = create_aadhaar_authenticity(
            aadhaar=cleaned,
            valid=valid,
            checksum_valid=checksum_valid,
            first_digit_valid=first_digit_valid,
        )

        result: dict[str, object] = {
            "valid": valid,
            "masked": masked,
            "checksum_valid": checksum_valid,
            "first_digit_valid": first_digit_valid,
            "errors": errors,
            "disclaimer": DISCLAIMER,
            "authenticity": auth,
        }
        if warnings:
            result["warnings"] = warnings
        return result

    except Exception as exc:
        cleaned = re.sub(r"[\s\-]", "", str(aadhaar).strip()) if aadhaar else ""
        masked_exc = mask_aadhaar_text(str(exc))
        return {
            "valid": False,
            "masked": _mask_aadhaar(cleaned) if cleaned else "",
            "checksum_valid": False,
            "first_digit_valid": False,
            "errors": [f"Aadhaar validation failed: {masked_exc}"],
            "disclaimer": DISCLAIMER,
            "authenticity": create_aadhaar_authenticity(
                aadhaar=cleaned,
                valid=False,
                checksum_valid=False,
                first_digit_valid=False,
            ),
        }
