"""EPF establishment code validator."""

from __future__ import annotations

import re
from typing import Any

EPF_RE = re.compile(r"^\d{2}/\d{5,6}/\d{5,6}/\d{3}$")


def validate_epf_code(code: str) -> dict[str, Any]:
    """Validate EPF establishment code format.

    Args:
        code: EPF establishment code (XX/XXXXX/XXXXXX/XXX).

    Returns:
        Dict with validation result, parsed components, and errors.
    """
    normalized = code.strip().upper().replace(" ", "")

    if not EPF_RE.match(normalized):
        return {
            "valid": False,
            "code": code,
            "normalized_input": normalized,
            "errors": ["Invalid EPF format. Expected: XX/XXXXX/XXXXXX/XXX"],
        }

    parts = normalized.split("/")
    return {
        "valid": True,
        "code": code,
        "normalized_input": normalized,
        "region_code": parts[0],
        "office_code": parts[1],
        "establishment_code": parts[2],
        "extension": parts[3],
        "errors": [],
    }
