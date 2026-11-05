"""PAN validation logic."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.authenticity.rules import create_pan_authenticity
from mcp_india_stack.tools import PAN_ENTITY_TYPE_LABELS
from mcp_india_stack.utils.responses import build_response

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


def validate_pan(pan: str, verify_online: bool = False) -> dict[str, Any]:
    """Validate PAN format and decode entity type.

    Note: PAN check character is not publicly algorithmic, so only structural
    validation is performed.
    """
    if pan is None:
        auth = create_pan_authenticity(pan="", valid=False)
        return _flatten(
            build_response(
                success=False,
                data={"valid": False},
                errors=["PAN is required"],
                source="offline_static",
                authenticity=auth,
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
        auth = create_pan_authenticity(pan=value, valid=False)
        return _flatten(
            build_response(
                success=False,
                data={"valid": False, "pan": value, "checksum_verifiable": False},
                errors=errors,
                warnings=warnings,
                source="offline_static",
                authenticity=auth,
            )
        )

    entity_code = value[3]
    entity_type = PAN_ENTITY_TYPE_LABELS.get(entity_code, "Unknown")
    if entity_type == "Unknown":
        warnings.append("PAN entity code is not in the common official list")

    if value == "AAAAA9999A":
        warnings.append("This PAN is a known dummy placeholder pattern")

    provider_res = None
    if verify_online:
        from mcp_india_stack.authenticity.providers.registry import execute_provider_verification

        provider_res = execute_provider_verification("pan", value)

    auth = create_pan_authenticity(
        pan=value,
        valid=True,
        entity_code=entity_code,
        entity_type=entity_type,
        verify_online=verify_online,
        provider_result=provider_res,
    )

    data_payload: dict[str, Any] = {
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
    }
    if provider_res is not None:
        data_payload["registry_status"] = provider_res.registry_status or provider_res.status.value

    return _flatten(
        build_response(
            success=True,
            data=data_payload,
            warnings=warnings,
            source="live" if verify_online else "offline_static",
            validated_by=["format_check"],
            authenticity=auth,
        )
    )
