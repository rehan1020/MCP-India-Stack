"""Pincode lookup logic."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.tools.state_code import decode_state_code
from mcp_india_stack.utils.loader import load_pincode_index, load_state_codes

PIN_RE = re.compile(r"^[0-9]{6}$")


def _state_to_code(state_name: str) -> str | None:
    table = load_state_codes()
    lookup = {v["state_name"].lower(): k for k, v in table.items()}
    return lookup.get(state_name.lower())


def lookup_pincode(pincode: str | int) -> dict[str, Any]:
    """Lookup Indian pincode and return all mapped post offices."""
    if pincode is None:
        return {"found": False, "errors": ["Pincode is required"]}

    value = str(pincode).strip().replace(" ", "").replace("-", "")
    if value.isdigit() and len(value) < 6:
        value = value.zfill(6)

    errors: list[str] = []
    warnings: list[str] = []
    if not PIN_RE.match(value):
        errors.append("Pincode must be exactly 6 digits")
        return {"found": False, "pincode": value, "errors": errors, "warnings": warnings}

    records = load_pincode_index().get(value, [])
    if not records:
        return {
            "found": False,
            "pincode": value,
            "errors": ["Pincode not found in bundled dataset"],
            "warnings": warnings,
        }

    state = records[0].get("StateName", "")
    district = records[0].get("DistrictName", "")
    region = records[0].get("Region", "")
    circle = records[0].get("Circle", "")
    division = records[0].get("Division", "")

    inconsistent_states = {r.get("StateName", "") for r in records}
    if len(inconsistent_states) > 1:
        warnings.append("Data quality warning: multiple states found for same pincode")

    state_code = _state_to_code(state)
    state_meta = decode_state_code(state_code) if state_code else {"found": False}

    offices = [
        {
            "name": r.get("OfficeName", ""),
            "type": r.get("OfficeType", ""),
            "delivery": r.get("Delivery", ""),
            "taluk": r.get("Taluk", ""),
        }
        for r in records
    ]

    return {
        "found": True,
        "pincode": value,
        "state": state,
        "district": district,
        "region": region,
        "circle": circle,
        "division": division,
        "state_code": state_meta.get("state_code"),
        "post_offices": offices,
        "errors": errors,
        "warnings": warnings,
    }
