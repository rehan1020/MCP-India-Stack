"""GSTIN validation and decoding."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.state_code import decode_state_code

BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^[0-9A-Z]{15}$")
PAN_BLOCK_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


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


def validate_gstin(gstin: str) -> dict[str, Any]:
    """Validate GSTIN, decode structure, and verify checksum."""
    if gstin is None:
        return {"valid": False, "errors": ["GSTIN is required"]}

    value = str(gstin).strip().upper()
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("GSTIN cannot be empty")
    elif len(value) != 15:
        errors.append("GSTIN must be exactly 15 characters")
    elif not GSTIN_RE.match(value):
        errors.append("GSTIN must contain only uppercase letters and digits")

    if errors:
        return {"valid": False, "gstin": value, "errors": errors, "warnings": warnings}

    state_decode = decode_state_code(value[:2])
    if not state_decode.get("found"):
        errors.append("GSTIN state code is invalid")

    pan_block = value[2:12]
    pan_check = validate_pan(pan_block)
    if not pan_check.get("valid"):
        errors.append("Embedded PAN block is invalid")

    entity_number = value[12]
    if entity_number not in BASE36[1:]:
        errors.append("13th character (entity number) is invalid")

    if value[13] != "Z":
        errors.append("14th character must be Z for standard GSTIN structure")

    expected_checksum = compute_gstin_checksum(value[:14])
    checksum_valid = expected_checksum == value[14]
    if not checksum_valid:
        errors.append("Checksum character is invalid")

    category = _classify_category(value)
    format_validity = "full" if category == "standard" else "limited"
    if category != "standard":
        warnings.append(
            "Detected special GSTIN category; v1 applies limited validation beyond core checks"
        )

    return {
        "valid": len(errors) == 0,
        "gstin": value,
        "state_code": value[:2],
        "state_name": state_decode.get("state_name"),
        "pan": pan_block,
        "entity_number": entity_number,
        "checksum_valid": checksum_valid,
        "expected_checksum": expected_checksum,
        "category": category,
        "format_validity": format_validity,
        "errors": errors,
        "warnings": warnings,
    }
