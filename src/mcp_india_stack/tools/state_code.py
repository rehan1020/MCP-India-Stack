"""State code decoding utilities."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.loader import load_state_codes

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z0-9]{13}$")


def decode_state_code(value: str) -> dict[str, Any]:
    """Decode a GST state code from a 2-digit code or a GSTIN-like identifier.

    Args:
            value: Two-digit state code or GSTIN string.

    Returns:
            Decoded state metadata with found flag and optional error.
    """
    if value is None:
        return {"found": False, "error": "state code input is required"}

    raw = str(value).strip().upper()
    if not raw:
        return {"found": False, "error": "state code input cannot be empty"}

    code = raw
    if len(raw) >= 2 and raw[:2].isdigit() and (len(raw) == 2 or GSTIN_RE.match(raw)):
        code = raw[:2]

    table = load_state_codes()
    item = table.get(code)
    if not item:
        return {"found": False, "state_code": code, "error": "unknown GST state code"}

    return {
        "found": True,
        "state_code": code,
        "state_name": item["state_name"],
        "abbreviation": item["abbreviation"],
        "capital": item["capital"],
        "gst_zone": item["gst_zone"],
    }
