"""LLPIN (Limited Liability Partnership Identification Number) validator."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.authenticity.rules import create_llpin_authenticity

DISCLAIMER = "Format validation only. Verify LLP status on MCA portal."


def validate_llpin(llpin: str) -> dict[str, Any]:
    """Validate LLPIN format.

    Args:
        llpin: LLPIN in format AAA-XXXX

    Returns:
        Dict with validation and segments.
    """
    cleaned = (llpin or "").strip().upper().replace(" ", "").replace("-", "")

    if not re.match(r"^[A-Z]{3}[0-9]{4}$", cleaned):
        auth = create_llpin_authenticity(llpin=cleaned, valid=False)
        return {
            "valid": False,
            "error": "Invalid LLPIN format",
            "disclaimer": DISCLAIMER,
            "authenticity": auth,
        }

    auth = create_llpin_authenticity(llpin=cleaned, valid=True)
    return {
        "valid": True,
        "llpin": f"{cleaned[:3]}-{cleaned[3:]}",
        "prefix": cleaned[:3],
        "serial": cleaned[3:],
        "note": "Format validation only. Verify LLP status on MCA portal.",
        "disclaimer": DISCLAIMER,
        "authenticity": auth,
    }
