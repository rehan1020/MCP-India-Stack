"""PAN entity type decoding from 4th character."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.utils.responses import build_response


def decode_pan_type(pan: str) -> dict[str, Any]:
    """Decode PAN entity type from 4th character."""
    result = validate_pan(pan)
    if result.get("success"):
        entity_code = result.get("data", {}).get("entity_code", "")
        entity_types = {
            "P": ("Individual", "NRI requires Form 60/61"),
            "C": ("Company", "Requires DIN for directors"),
            "H": ("Hindu Undivided Family (HUF)", "HUF"),
            "F": ("Firm", "Partnership/LLP"),
            "A": ("Association of Persons (AOP)", "AOP"),
            "B": ("Body of Individuals (BOI)", "BOI"),
            "G": ("Government", "Central/State"),
            "J": ("Artificial Juridical Person", "AJP"),
            "L": ("Local Authority", "Panchayat/Municipal"),
            "T": ("Trust", "Trust"),
            "E": ("Limited Liability Partnership (LLP)", "LLP"),
        }
        entity_label, kyc_hint = entity_types.get(entity_code, ("Unknown", ""))
        return build_response(
            success=True,
            data={
                "pan": pan.upper(),
                "entity_type_code": entity_code,
                "entity_type_label": entity_label,
                "kyc_routing_hint": kyc_hint,
                "normalized_input": pan.upper().strip(),
            },
            validated_by=["format", "checksum"],
            source="offline_algorithm",
        )
    return build_response(
        success=False, data=result, errors=result.get("errors", []), source="offline_algorithm"
    )
