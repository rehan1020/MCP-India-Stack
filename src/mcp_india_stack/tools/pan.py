"""PAN validation logic."""

from __future__ import annotations

import re
from typing import Any

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

ENTITY_TYPES = {
    "P": "Individual",
    "C": "Company",
    "H": "HUF",
    "F": "Firm",
    "A": "Association of Persons",
    "T": "Trust",
    "B": "Body of Individuals",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government",
}


def validate_pan(pan: str) -> dict[str, Any]:
    """Validate PAN format and decode entity type.

    Note: PAN check character is not publicly algorithmic, so only structural
    validation is possible in offline mode.
    """
    if pan is None:
        return {"valid": False, "errors": ["PAN is required"]}

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
        return {
            "valid": False,
            "pan": value,
            "errors": errors,
            "warnings": warnings,
            "checksum_verifiable": False,
        }

    entity_code = value[3]
    entity_type = ENTITY_TYPES.get(entity_code, "Unknown")
    if entity_type == "Unknown":
        warnings.append("PAN entity code is not in the common official list")

    if value == "AAAAA9999A":
        warnings.append("This PAN is a known dummy placeholder pattern")

    return {
        "valid": True,
        "pan": value,
        "entity_code": entity_code,
        "entity_type": entity_type,
        "series": value[:3],
        "name_initial": value[4],
        "sequence": value[5:9],
        "check_character": value[9],
        "checksum_verifiable": False,
        "errors": errors,
        "warnings": warnings,
    }
