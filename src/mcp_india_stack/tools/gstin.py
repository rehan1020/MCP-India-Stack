"""GSTIN validation and decoding."""

from __future__ import annotations

import os
import re
from typing import Any

from mcp_india_stack.authenticity.rules import create_gstin_authenticity
from mcp_india_stack.normalization import normalize_gstin
from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.state_code import decode_state_code
from mcp_india_stack.utils.responses import build_response

BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^[0-9A-Z]{15}$")
PAN_BLOCK_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

_LIVE_LOOKUP_ENABLED = os.environ.get("MCP_INDIA_STACK_LIVE_LOOKUP") == "1"


def _char_to_value(ch: str) -> int:
    return BASE36.index(ch)


def compute_gstin_checksum(first_14: str) -> str:
    """Compute GSTIN checksum for first 14 characters."""
    total = 0
    factor = 1
    for ch in first_14:
        code_point = _char_to_value(ch)
        addend = factor * code_point
        factor = 2 if factor == 1 else 1
        addend = (addend // 36) + (addend % 36)
        total += addend
    remainder = total % 36
    check_code_point = (36 - remainder) % 36
    return BASE36[check_code_point]


def _classify_category(gstin: str) -> str:
    if gstin.startswith("99"):
        return "composite_taxpayer"
    pan_block = gstin[2:12]
    if pan_block.startswith("NR"):
        return "non_resident"
    if pan_block.startswith(("GOV", "DPT")):
        return "government_department"
    if not PAN_BLOCK_RE.match(pan_block):
        return "unknown_special"
    return "standard"


def validate_gstin(  # noqa: C901
    gstin: str,
    expected_entity_type: str | None = None,
    verify_online: bool = False,
) -> dict[str, Any]:
    """Validate GSTIN, decode structure, and verify checksum.

    Args:
        gstin: 15-character GSTIN to validate.
        expected_entity_type: Optional expected entity type (e.g. 'P', 'C') to match against PAN.
        verify_online: Optional opt-in live registry attestation (A4 level).

    Returns:
        Dict with validity, state decode, embedded PAN, entity number,
        category, checksum info, live_verified flag, and verification_source.
    """
    if gstin is None:
        auth = create_gstin_authenticity(
            gstin="",
            valid=False,
            state_valid=False,
            pan_valid=False,
            entity_num_valid=False,
            char14_valid=False,
            checksum_valid=False,
            expected_entity_type=expected_entity_type,
        )
        return build_response(
            success=False,
            data={"valid": False, "live_verified": False},
            errors=["GSTIN is required"],
            source="offline_static",
            authenticity=auth,
        )

    normalized = normalize_gstin(gstin)
    value = normalized["normalized_input"]
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("GSTIN cannot be empty")
    elif len(value) != 15:
        errors.append("GSTIN must be exactly 15 characters")
    elif not GSTIN_RE.match(value):
        errors.append("GSTIN must contain only uppercase letters and digits")

    if errors:
        auth = create_gstin_authenticity(
            gstin=value or "",
            valid=False,
            state_valid=False,
            pan_valid=False,
            entity_num_valid=False,
            char14_valid=False,
            checksum_valid=False,
            expected_entity_type=expected_entity_type,
        )
        return build_response(
            success=False,
            data={"valid": False, "gstin": value, "live_verified": False},
            errors=errors,
            warnings=warnings,
            source="offline_static",
            authenticity=auth,
        )

    state_decode = decode_state_code(value[:2])
    state_valid = bool(state_decode.get("data", {}).get("found"))
    if not state_valid:
        errors.append("GSTIN state code is invalid")

    pan_block = value[2:12]
    pan_check = validate_pan(pan_block)
    pan_valid = bool(pan_check.get("data", {}).get("valid"))
    if not pan_valid:
        errors.append("Embedded PAN block is invalid")

    entity_number = value[12]
    entity_num_valid = entity_number in BASE36[1:]
    if not entity_num_valid:
        errors.append("13th character (entity number) is invalid")

    char14_valid = value[13] == "Z"
    if not char14_valid:
        errors.append("14th character must be Z for standard GSTIN structure")

    expected_checksum = compute_gstin_checksum(value[:14])
    checksum_valid = expected_checksum == value[14]
    if not checksum_valid:
        errors.append("Checksum character is invalid")

    if expected_entity_type and pan_block and len(pan_block) >= 4:
        if pan_block[3].upper() != expected_entity_type.strip().upper():
            errors.append(
                f"PAN 4th character '{pan_block[3]}' does not match "
                f"expected entity type '{expected_entity_type}'"
            )

    category = _classify_category(value)
    format_validity = "full" if category == "standard" else "limited"
    if category != "standard":
        warnings.append(
            "Detected special GSTIN category; v1 applies limited validation beyond core checks"
        )

    valid = len(errors) == 0

    provider_res = None
    if verify_online and valid:
        from mcp_india_stack.authenticity.providers.registry import execute_provider_verification

        provider_res = execute_provider_verification("gstin", value)

    auth = create_gstin_authenticity(
        gstin=value,
        valid=valid,
        state_valid=state_valid,
        pan_valid=pan_valid,
        entity_num_valid=entity_num_valid,
        char14_valid=char14_valid,
        checksum_valid=checksum_valid,
        pan_block=pan_block,
        expected_entity_type=expected_entity_type,
        verify_online=verify_online,
        provider_result=provider_res,
    )

    data_payload: dict[str, Any] = {
        "valid": valid,
        "gstin": value,
        "state_code": value[:2],
        "state_name": state_decode.get("data", {}).get("state_name"),
        "pan": pan_block,
        "entity_number": entity_number,
        "checksum_valid": checksum_valid,
        "expected_checksum": expected_checksum,
        "category": category,
        "format_validity": format_validity,
        "live_verified": _LIVE_LOOKUP_ENABLED or (verify_online and provider_res is not None),
        "normalized_input": value,
    }
    if provider_res is not None:
        data_payload["registry_status"] = provider_res.registry_status or provider_res.status.value

    return build_response(
        success=valid,
        data=data_payload,
        errors=errors,
        warnings=warnings,
        source="live" if (_LIVE_LOOKUP_ENABLED or verify_online) else "offline_static",
        validated_by=["format_check", "checksum"],
        authenticity=auth,
    )
