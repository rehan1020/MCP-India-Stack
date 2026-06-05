"""TAN (Tax Deduction Account Number) validator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Format validation only. Does not verify active status on TRACES."


def validate_tan(tan: str) -> dict[str, Any]:
    """Validate TAN format.

    Args:
        tan: 10-character TAN

    Returns:
        Dict with validation and decoded segments.
    """
    import re

    tan_clean = tan.strip().upper().replace(" ", "").replace("-", "")

    if not re.match(r"^[A-Z]{4}[0-9]{5}[A-Z]{1}$", tan_clean):
        return {"valid": False, "error": "Invalid TAN format", "disclaimer": DISCLAIMER}

    return {
        "valid": True,
        "tan": tan_clean,
        "ao_code": tan_clean[:3],
        "entity_initial": tan_clean[3],
        "serial": tan_clean[4:9],
        "check_char": tan_clean[9],
        "note": "Format validation only. Does not verify active status on TRACES.",
        "disclaimer": DISCLAIMER,
    }
