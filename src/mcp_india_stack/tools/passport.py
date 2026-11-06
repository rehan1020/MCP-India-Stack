"""Indian passport number format validation."""

from __future__ import annotations

import re

from mcp_india_stack.authenticity.rules import create_passport_authenticity
from mcp_india_stack.utils.responses import build_response

PASSPORT_RE = re.compile(r"^[A-Z][0-9]{7}$")

DISCLAIMER = "Format validation only. Cannot verify passport validity or status."


def validate_passport(passport_number: str) -> dict[str, object]:
    """Validate an Indian passport number format.

    Format: 1 uppercase letter (series) + 7 digits (sequential number) = 8 characters.
    No publicly available checksum — format validation only.

    Args:
        passport_number: Indian passport number string.

    Returns:
        Dict with validation results.
    """
    try:
        if passport_number is None:
            auth = create_passport_authenticity(passport="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "passport_number": "", "series_letter": "", "serial": ""},
                errors=["Passport number is required"],
                source="offline_static",
                authenticity=auth,
            )

        cleaned = str(passport_number).strip().upper()
        errors: list[str] = []

        if not cleaned:
            auth = create_passport_authenticity(passport="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "passport_number": "", "series_letter": "", "serial": ""},
                errors=["Passport number cannot be empty"],
                source="offline_static",
                authenticity=auth,
            )

        if len(cleaned) != 8:
            errors.append(
                f"Indian passport number must be exactly 8 characters, got {len(cleaned)}"
            )
            auth = create_passport_authenticity(passport=cleaned, valid=False)
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "passport_number": cleaned,
                    "series_letter": "",
                    "serial": "",
                },
                errors=errors,
                source="offline_static",
                authenticity=auth,
            )

        if not PASSPORT_RE.match(cleaned):
            errors.append("Passport number must be 1 uppercase letter followed by 7 digits")
            auth = create_passport_authenticity(passport=cleaned, valid=False)
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "passport_number": cleaned,
                    "series_letter": "",
                    "serial": "",
                },
                errors=errors,
                source="offline_static",
                authenticity=auth,
            )

        auth = create_passport_authenticity(passport=cleaned, valid=True)
        return build_response(
            success=True,
            data={
                "valid": True,
                "passport_number": cleaned,
                "series_letter": cleaned[0],
                "serial": cleaned[1:],
            },
            source="offline_static",
            validated_by=["format_check"],
            authenticity=auth,
        )

    except Exception as exc:
        auth = create_passport_authenticity(
            passport=str(passport_number) if passport_number else "", valid=False
        )
        return build_response(
            success=False,
            data={
                "valid": False,
                "passport_number": str(passport_number) if passport_number else "",
                "series_letter": "",
                "serial": "",
            },
            errors=[f"Passport validation failed: {exc}"],
            source="offline_static",
            authenticity=auth,
        )
