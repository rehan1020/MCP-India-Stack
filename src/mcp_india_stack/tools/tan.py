"""TAN (Tax Deduction Account Number) validator."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.authenticity.rules import create_tan_authenticity

DISCLAIMER = "Format validation only. Does not verify active status on TRACES."


def validate_tan(tan: str) -> dict[str, Any]:
    """Validate TAN format.

    Args:
        tan: 10-character TAN

    Returns:
        Dict with validation and decoded segments.
    """
    tan_clean = (tan or "").strip().upper().replace(" ", "").replace("-", "")

    if not re.match(r"^[A-Z]{4}[0-9]{5}[A-Z]{1}$", tan_clean):
        auth = create_tan_authenticity(tan=tan_clean, valid=False)
        return {
            "valid": False,
            "error": "Invalid TAN format",
            "disclaimer": DISCLAIMER,
            "authenticity": auth,
        }

    auth = create_tan_authenticity(tan=tan_clean, valid=True)
    return {
        "valid": True,
        "tan": tan_clean,
        "ao_code": tan_clean[:3],
        "entity_initial": tan_clean[3],
        "serial": tan_clean[4:9],
        "check_char": tan_clean[9],
        "note": "Format validation only. Does not verify active status on TRACES.",
        "disclaimer": DISCLAIMER,
        "authenticity": auth,
    }
