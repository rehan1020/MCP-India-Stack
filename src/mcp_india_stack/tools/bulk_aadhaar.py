"""Bulk Aadhaar validation using shared bounded executor."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.authenticity.models import summarize_authenticity_levels
from mcp_india_stack.authenticity.rules import create_aadhaar_authenticity
from mcp_india_stack.logging_filter import mask_aadhaar_text
from mcp_india_stack.tools.aadhaar import (
    _mask_aadhaar,
)
from mcp_india_stack.tools.aadhaar import (
    validate_aadhaar as core_validate_aadhaar,
)
from mcp_india_stack.tools.bulk_common import (
    execute_bulk_items,
    validate_bulk_bounds,
)

DISCLAIMER = (
    "Structural and Verhoeff checksum validation only. Not connected to UIDAI. "
    "In compliance with DPDP Act 2023, raw Aadhaar numbers are never stored or logged."
)


def _validate_single_aadhaar(aadhaar: str) -> dict[str, Any]:
    """Validate a single Aadhaar with error isolation."""
    try:
        result = core_validate_aadhaar(aadhaar)
        raw_errors = result.get("errors")
        err_list: list[Any] = raw_errors if isinstance(raw_errors, list) else []
        return {
            "masked": result.get("masked", ""),
            "valid": result.get("valid", False),
            "errors": [mask_aadhaar_text(str(e)) for e in err_list],
            "authenticity": result.get("authenticity"),
        }
    except Exception as exc:
        masked_input = _mask_aadhaar(str(aadhaar)) if aadhaar else ""
        auth = create_aadhaar_authenticity(
            aadhaar=str(aadhaar) if aadhaar else "",
            valid=False,
            checksum_valid=False,
            first_digit_valid=False,
        )
        return {
            "masked": masked_input,
            "valid": False,
            "errors": [f"Validation error: {mask_aadhaar_text(str(exc))}"],
            "authenticity": auth,
        }


def _aadhaar_fallback(val: Any, err: str) -> dict[str, Any]:
    """Fallback representation for failed or malformed Aadhaar item."""
    masked = _mask_aadhaar(str(val)) if val is not None else ""
    auth = create_aadhaar_authenticity(
        aadhaar=str(val) if val is not None else "",
        valid=False,
        checksum_valid=False,
        first_digit_valid=False,
    )
    return {
        "masked": masked,
        "valid": False,
        "errors": [mask_aadhaar_text(err)],
        "authenticity": auth,
    }


def bulk_validate_aadhaar(numbers: list[str]) -> dict[str, Any]:
    """Validate multiple Aadhaar numbers in parallel using ThreadPoolExecutor.

    UIDAI & DPDP Compliance:
    Validates structural format and Verhoeff checksum only. Not connected to UIDAI.
    In compliance with the Digital Personal Data Protection Act, 2023 (DPDP Act)
    and UIDAI guidelines, all Aadhaar outputs are masked to the last 4 digits and
    raw 12-digit numbers are never stored or logged.

    Args:
        numbers: List of Aadhaar numbers (with or without spaces/hyphens).

    Returns:
        Dict with per-Aadhaar results and valid/invalid counts.
    """
    is_valid, errors = validate_bulk_bounds(numbers, entity_name="Aadhaar")
    if not is_valid:
        return {
            "total": len(numbers) if isinstance(numbers, list) else 0,
            "valid_count": 0,
            "invalid_count": 0,
            "results": [],
            "errors": errors,
            "disclaimer": DISCLAIMER,
        }

    ordered_results = execute_bulk_items(
        items=numbers,
        validate_fn=_validate_single_aadhaar,
        fallback_fn=_aadhaar_fallback,
        entity_name="Aadhaar",
    )
    indexed_results = [{"index": idx, **r} for idx, r in enumerate(ordered_results)]
    valid_count = sum(1 for r in ordered_results if r.get("valid"))
    invalid_count = len(ordered_results) - valid_count
    summary = summarize_authenticity_levels(ordered_results)

    return {
        "total": len(numbers),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "results": indexed_results,
        "authenticity_summary": summary,
        "authenticity": {"summary": summary},
        "disclaimer": DISCLAIMER,
    }
