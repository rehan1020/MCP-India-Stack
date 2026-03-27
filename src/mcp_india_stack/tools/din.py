"""DIN (Director Identification Number) format validation."""

from __future__ import annotations

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
            return {
                "valid": False,
                "din": "",
                "errors": ["DIN is required"],
                "disclaimer": DISCLAIMER,
            }

        cleaned = str(din).strip()
        errors: list[str] = []

        if not cleaned:
            return {
                "valid": False,
                "din": "",
                "errors": ["DIN cannot be empty"],
                "disclaimer": DISCLAIMER,
            }

        # Strip non-numeric for normalization but check original
        if not cleaned.isdigit():
            return {
                "valid": False,
                "din": cleaned,
                "errors": ["DIN must contain only digits"],
                "disclaimer": DISCLAIMER,
            }

        # Zero-pad if shorter (e.g. leading zeros stripped)
        padded = cleaned.zfill(8)

        if len(cleaned) > 8:
            errors.append(
                f"DIN must be exactly 8 digits, got {len(cleaned)}"
            )
            return {
                "valid": False,
                "din": cleaned,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        if len(padded) != 8:
            errors.append(
                f"DIN must be exactly 8 digits, got {len(cleaned)}"
            )
            return {
                "valid": False,
                "din": padded,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        return {
            "valid": True,
            "din": padded,
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "valid": False,
            "din": str(din) if din else "",
            "errors": [f"DIN validation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
