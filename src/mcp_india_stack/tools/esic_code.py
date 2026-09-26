"""ESIC employer code validator."""

from __future__ import annotations

import re
from typing import Any

ESIC_RE = re.compile(r"^[\d]{2}-[\d]+-[\d]+$")


def validate_esic_code(code: str) -> dict[str, Any]:
    """Validate ESIC employer code format.

    Args:
        code: ESIC employer code (XX-XXXXX-XXXXX).

    Returns:
        Dict with validation result, parsed components, and errors.
    """
    normalized = code.strip().upper().replace(" ", "")

    if not ESIC_RE.match(normalized):
        return {
            "valid": False,
            "code": code,
            "normalized_input": normalized,
            "errors": ["Invalid ESIC format. Expected: XX-XXXXX-XXXXX"],
        }

    parts = normalized.split("-")
    return {
        "valid": True,
        "code": code,
        "normalized_input": normalized,
        "regional_code": parts[0],
        "employer_code": parts[1],
        "sub_code": parts[2],
        "errors": [],
    }
