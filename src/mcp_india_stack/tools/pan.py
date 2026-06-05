"""PAN validation logic."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.tools import PAN_ENTITY_TYPE_LABELS
from mcp_india_stack.utils.responses import build_response

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


def validate_pan(pan: str) -> dict[str, Any]:
    """Validate PAN format and decode entity type.

    Note: PAN check character is not publicly algorithmic, so only structural
    validation is performed.
    """
    if pan is None:
        return _flatten(
            build_response(
                success=False,
                data={"valid": False},
                errors=["PAN is required"],
                source="offline_static",
            )
        )

    value = str(pan).strip().upper()
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("PAN cannot be empty")
    elif len(value) != 10:
        errors.append("PAN must be exactly 10 characters")
    elif not PAN_RE.match(value):
        errors.append("PAN must match format AAAAA9999A")

    if errors:
        return _flatten(
            build_response(
                success=False,
                data={"valid": False, "pan": value, "checksum_verifiable": False},
                errors=errors,
                warnings=warnings,
                source="offline_static",
            )
        )

    entity_code = value[3]
    entity_type = PAN_ENTITY_TYPE_LABELS.get(entity_code, "Unknown")
    if entity_type == "Unknown":
        warnings.append("PAN entity code is not in the common official list")

    if value == "AAAAA9999A":
        warnings.append("This PAN is a known dummy placeholder pattern")

    return _flatten(
        build_response(
            success=True,
            data={
                "valid": True,
                "pan": value,
                "entity_code": entity_code,
                "entity_type": entity_type,
                "series": value[:3],
                "name_initial": value[4],
                "sequence": value[5:9],
                "check_character": value[9],
                "checksum_verifiable": False,
                "normalized_input": value,
            },
            warnings=warnings,
            source="offline_static",
            validated_by=["format_check"],
        )
    )
