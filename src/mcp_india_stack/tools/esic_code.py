"""ESIC employer code validator."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.authenticity.rules import create_esic_authenticity
from mcp_india_stack.utils.responses import build_response

ESIC_RE = re.compile(r"^[\d]{2}-[\d]+-[\d]+$")


def validate_esic_code(code: str) -> dict[str, Any]:
    """Validate ESIC employer code format.

    Args:
        code: ESIC employer code (XX-XXXXX-XXXXX).

    Returns:
        Standard envelope with validation result and parsed components.
    """
    normalized = (code or "").strip().upper().replace(" ", "")

    if not ESIC_RE.match(normalized):
        auth = create_esic_authenticity(
            code=normalized,
            valid=False,
            region_valid=False,
        )
        return build_response(
            success=False,
            data={"code": code, "normalized_input": normalized},
            errors=["Invalid ESIC format. Expected: XX-XXXXX-XXXXX"],
            source="offline_algorithm",
            authenticity=auth,
        )

    parts = normalized.split("-")
    region_valid = parts[0].isdigit() and 1 <= int(parts[0]) <= 99
    auth = create_esic_authenticity(
        code=normalized,
        valid=True,
        region_valid=region_valid,
    )
    return build_response(
        success=True,
        data={
            "code": code,
            "normalized_input": normalized,
            "regional_code": parts[0],
            "employer_code": parts[1],
            "sub_code": parts[2],
        },
        validated_by=["format"],
        source="offline_algorithm",
        authenticity=auth,
    )
