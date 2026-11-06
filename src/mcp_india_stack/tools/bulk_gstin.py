"""Bulk GSTIN validation using shared bounded executor."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.authenticity.models import summarize_authenticity_levels
from mcp_india_stack.authenticity.rules import create_gstin_authenticity
from mcp_india_stack.tools.bulk_common import (
    execute_bulk_items,
    validate_bulk_bounds,
)
from mcp_india_stack.tools.gstin import validate_gstin as core_validate_gstin
from mcp_india_stack.utils.responses import build_response


def _validate_single_gstin(gstin: str) -> dict[str, Any]:
    """Validate a single GSTIN with error isolation."""
    try:
        return core_validate_gstin(gstin)
    except Exception as exc:
        return _gstin_fallback(gstin, f"Validation error: {exc}")


def _gstin_fallback(val: Any, err: str) -> dict[str, Any]:
    """Fallback representation for failed or malformed GSTIN item."""
    gstin_str = str(val) if val is not None else ""
    auth = create_gstin_authenticity(
        gstin=gstin_str,
        valid=False,
        state_valid=False,
        pan_valid=False,
        entity_num_valid=False,
        char14_valid=False,
        checksum_valid=False,
    )
    return {
        "valid": False,
        "gstin": gstin_str,
        "errors": [err],
        "warnings": [],
        "live_verified": False,
        "verification_source": "offline",
        "authenticity": auth,
    }


def bulk_validate_gstin(gstins: list[str]) -> dict[str, Any]:
    """Validate multiple GSTINs in parallel using shared ThreadPoolExecutor.

    Args:
        gstins: List of 15-character GSTIN strings.

    Returns:
        Standard envelope with per-GSTIN results, valid/invalid counts.
    """
    is_valid, errors = validate_bulk_bounds(gstins, entity_name="GSTIN")
    if not is_valid:
        return build_response(
            success=False,
            data=None,
            errors=errors,
            source="offline_algorithm",
        )

    ordered_results = execute_bulk_items(
        items=gstins,
        validate_fn=_validate_single_gstin,
        fallback_fn=_gstin_fallback,
        entity_name="GSTIN",
    )
    valid_count = sum(1 for r in ordered_results if r.get("valid"))
    invalid_count = len(ordered_results) - valid_count
    summary = summarize_authenticity_levels(ordered_results)

    return build_response(
        success=True,
        data={
            "results": ordered_results,
            "total": len(gstins),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "authenticity_summary": summary,
        },
        source="offline_algorithm",
        authenticity={"summary": summary},
    )
