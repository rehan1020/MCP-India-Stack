"""Voter ID (EPIC) format validation."""

from __future__ import annotations

import re

EPIC_RE = re.compile(r"^[A-Z]{3}[0-9]{7}$")
ALPHANUMERIC_RE = re.compile(r"^[A-Z0-9]{10}$")

DISCLAIMER = "Format validation only. Cannot verify voter registration status."


def validate_voter_id(voter_id: str) -> dict[str, object]:
    """Validate an Indian Voter ID (EPIC) number format.

    Standard format: 3 uppercase letters + 7 digits (10 characters total).
    Legacy formats issued before 2017 ERONET standardisation may differ.

    Args:
        voter_id: EPIC number string.

    Returns:
        Dict with validation results.
    """
    try:
        if voter_id is None:
            return {
                "valid": False,
                "epic": "",
                "prefix": "",
                "serial": "",
                "format": "",
                "errors": ["Voter ID is required"],
                "disclaimer": DISCLAIMER,
            }

        cleaned = str(voter_id).strip().upper()
        errors: list[str] = []

        if not cleaned:
            return {
                "valid": False,
                "epic": "",
                "prefix": "",
                "serial": "",
                "format": "",
                "errors": ["Voter ID cannot be empty"],
                "disclaimer": DISCLAIMER,
            }

        # Standard format check
        if EPIC_RE.match(cleaned):
            return {
                "valid": True,
                "epic": cleaned,
                "prefix": cleaned[:3],
                "serial": cleaned[3:],
                "format": "standard",
                "errors": [],
                "disclaimer": DISCLAIMER,
            }

        # Legacy format detection
        if len(cleaned) == 10 and ALPHANUMERIC_RE.match(cleaned):
            return {
                "valid": False,
                "epic": cleaned,
                "prefix": cleaned[:3],
                "serial": cleaned[3:],
                "format": "legacy_possible",
                "errors": [
                    "Input may be a legacy EPIC format issued before "
                    "2017 standardisation. Format cannot be validated."
                ],
                "disclaimer": DISCLAIMER,
            }

        # Invalid
        if len(cleaned) != 10:
            errors.append(
                f"Voter ID must be exactly 10 characters, got {len(cleaned)}"
            )
        else:
            errors.append(
                "Voter ID must match pattern: 3 uppercase letters followed by 7 digits"
            )

        return {
            "valid": False,
            "epic": cleaned,
            "prefix": "",
            "serial": "",
            "format": "",
            "errors": errors,
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "valid": False,
            "epic": str(voter_id) if voter_id else "",
            "prefix": "",
            "serial": "",
            "format": "",
            "errors": [f"Voter ID validation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
