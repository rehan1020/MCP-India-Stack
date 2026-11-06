"""Voter ID (EPIC) format validation."""

from __future__ import annotations

import re

from mcp_india_stack.authenticity.rules import create_voter_id_authenticity
from mcp_india_stack.utils.responses import build_response

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
            auth = create_voter_id_authenticity(voter_id="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "epic": "", "prefix": "", "serial": "", "format": ""},
                errors=["Voter ID is required"],
                source="offline_static",
                authenticity=auth,
            )

        cleaned = str(voter_id).strip().upper()
        errors: list[str] = []

        if not cleaned:
            auth = create_voter_id_authenticity(voter_id="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "epic": "", "prefix": "", "serial": "", "format": ""},
                errors=["Voter ID cannot be empty"],
                source="offline_static",
                authenticity=auth,
            )

        # Standard format check
        if EPIC_RE.match(cleaned):
            auth = create_voter_id_authenticity(
                voter_id=cleaned, valid=True, format_type="standard"
            )
            return build_response(
                success=True,
                data={
                    "valid": True,
                    "epic": cleaned,
                    "prefix": cleaned[:3],
                    "serial": cleaned[3:],
                    "format": "standard",
                },
                source="offline_static",
                validated_by=["format_check"],
                authenticity=auth,
            )

        # Legacy format detection
        if len(cleaned) == 10 and ALPHANUMERIC_RE.match(cleaned):
            auth = create_voter_id_authenticity(
                voter_id=cleaned, valid=False, format_type="legacy_possible"
            )
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "epic": cleaned,
                    "prefix": cleaned[:3],
                    "serial": cleaned[3:],
                    "format": "legacy_possible",
                },
                errors=[
                    "Input may be a legacy EPIC format issued before "
                    "2017 standardisation. Format cannot be validated."
                ],
                source="offline_static",
                authenticity=auth,
            )

        # Invalid
        if len(cleaned) != 10:
            errors.append(f"Voter ID must be exactly 10 characters, got {len(cleaned)}")
        else:
            errors.append("Voter ID must match pattern: 3 uppercase letters followed by 7 digits")

        auth = create_voter_id_authenticity(voter_id=cleaned, valid=False)
        return build_response(
            success=False,
            data={"valid": False, "epic": cleaned, "prefix": "", "serial": "", "format": ""},
            errors=errors,
            source="offline_static",
            authenticity=auth,
        )

    except Exception as exc:
        auth = create_voter_id_authenticity(voter_id=str(voter_id) if voter_id else "", valid=False)
        return build_response(
            success=False,
            data={
                "valid": False,
                "epic": str(voter_id) if voter_id else "",
                "prefix": "",
                "serial": "",
                "format": "",
            },
            errors=[f"Voter ID validation failed: {exc}"],
            source="offline_static",
            authenticity=auth,
        )
