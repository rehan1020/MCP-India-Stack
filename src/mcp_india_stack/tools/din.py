"""DIN (Director Identification Number) format validation."""

from __future__ import annotations

from mcp_india_stack.authenticity.rules import create_din_authenticity
from mcp_india_stack.utils.responses import build_response

DISCLAIMER = "Format validation only. Cannot verify director status with MCA."


def validate_din(din: str) -> dict[str, object]:
    """Validate an Indian DIN (Director Identification Number).

    DIN is exactly 8 digits. No publicly documented checksum — length and
    numeric validation only.

    Args:
        din: DIN string to validate.

    Returns:
        Dict with validation results.
    """
    try:
        if din is None:
            auth = create_din_authenticity(din="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "din": ""},
                errors=["DIN is required"],
                source="offline_static",
                authenticity=auth,
            )

        cleaned = str(din).strip()
        errors: list[str] = []

        if not cleaned:
            auth = create_din_authenticity(din="", valid=False)
            return build_response(
                success=False,
                data={"valid": False, "din": ""},
                errors=["DIN cannot be empty"],
                source="offline_static",
                authenticity=auth,
            )

        # Strip non-numeric for normalization but check original
        if not cleaned.isdigit():
            auth = create_din_authenticity(din=cleaned, valid=False)
            return build_response(
                success=False,
                data={"valid": False, "din": cleaned},
                errors=["DIN must contain only digits"],
                source="offline_static",
                authenticity=auth,
            )

        # Zero-pad if shorter (e.g. leading zeros stripped)
        padded = cleaned.zfill(8)

        if len(cleaned) > 8:
            errors.append(f"DIN must be exactly 8 digits, got {len(cleaned)}")
            auth = create_din_authenticity(din=cleaned, valid=False)
            return build_response(
                success=False,
                data={"valid": False, "din": cleaned},
                errors=errors,
                source="offline_static",
                authenticity=auth,
            )

        if len(padded) != 8:
            errors.append(f"DIN must be exactly 8 digits, got {len(cleaned)}")
            auth = create_din_authenticity(din=padded, valid=False)
            return build_response(
                success=False,
                data={"valid": False, "din": padded},
                errors=errors,
                source="offline_static",
                authenticity=auth,
            )

        auth = create_din_authenticity(din=padded, valid=True)
        return build_response(
            success=True,
            data={
                "valid": True,
                "din": padded,
            },
            source="offline_static",
            validated_by=["format_check"],
            authenticity=auth,
        )

    except Exception as exc:
        auth = create_din_authenticity(din=str(din) if din else "", valid=False)
        return build_response(
            success=False,
            data={"valid": False, "din": str(din) if din else ""},
            errors=[f"DIN validation failed: {exc}"],
            source="offline_static",
            authenticity=auth,
        )
