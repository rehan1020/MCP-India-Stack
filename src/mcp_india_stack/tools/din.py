"""DIN (Director Identification Number) format validation."""

from __future__ import annotations

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
            return build_response(
                success=False,
                data={"valid": False, "din": ""},
                errors=["DIN is required"],
                source="offline_static",
            )

        cleaned = str(din).strip()
        errors: list[str] = []

        if not cleaned:
            return build_response(
                success=False,
                data={"valid": False, "din": ""},
                errors=["DIN cannot be empty"],
                source="offline_static",
            )

        # Strip non-numeric for normalization but check original
        if not cleaned.isdigit():
            return build_response(
                success=False,
                data={"valid": False, "din": cleaned},
                errors=["DIN must contain only digits"],
                source="offline_static",
            )

        # Zero-pad if shorter (e.g. leading zeros stripped)
        padded = cleaned.zfill(8)

        if len(cleaned) > 8:
            errors.append(f"DIN must be exactly 8 digits, got {len(cleaned)}")
            return build_response(
                success=False,
                data={"valid": False, "din": cleaned},
                errors=errors,
                source="offline_static",
            )

        if len(padded) != 8:
            errors.append(f"DIN must be exactly 8 digits, got {len(cleaned)}")
            return build_response(
                success=False,
                data={"valid": False, "din": padded},
                errors=errors,
                source="offline_static",
            )

        return build_response(
            success=True,
            data={
                "valid": True,
                "din": padded,
            },
            source="offline_static",
            validated_by=["format_check"],
        )

    except Exception as exc:
        return build_response(
            success=False,
            data={"valid": False, "din": str(din) if din else ""},
            errors=[f"DIN validation failed: {exc}"],
            source="offline_static",
        )
