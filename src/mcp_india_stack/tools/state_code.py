"""State code decoding utilities."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.loader import load_state_codes
from mcp_india_stack.utils.responses import build_response

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z0-9]{13}$")


def decode_state_code(value: str) -> dict[str, Any]:
    """Decode a GST state code from a 2-digit code or a GSTIN-like identifier.

    Args:
            value: Two-digit state code or GSTIN string.

    Returns:
            Decoded state metadata with found flag and optional error.
    """
    if value is None:
        return build_response(
            success=False,
            data={"found": False},
            errors=["state code input is required"],
            source="offline_static",
        )

    raw = str(value).strip().upper()
    if not raw:
        return build_response(
            success=False,
            data={"found": False},
            errors=["state code input cannot be empty"],
            source="offline_static",
        )

    code = raw
    if len(raw) >= 2 and raw[:2].isdigit() and (len(raw) == 2 or GSTIN_RE.match(raw)):
        code = raw[:2]

    table = load_state_codes()
    item = table.get(code)
    if not item:
        return build_response(
            success=False,
            data={"found": False, "state_code": code},
            errors=["unknown GST state code"],
            source="offline_static",
        )

    return build_response(
        success=True,
        data={
            "found": True,
            "state_code": code,
            "state_name": item["state_name"],
            "abbreviation": item["abbreviation"],
            "capital": item["capital"],
            "gst_zone": item["gst_zone"],
        },
        source="offline_static",
        validated_by=["db_lookup"],
    )
