"""Bulk PAN validation using shared bounded executor."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.authenticity.models import summarize_authenticity_levels
from mcp_india_stack.authenticity.rules import create_pan_authenticity
from mcp_india_stack.tools.bulk_common import (
    execute_bulk_items,
    validate_bulk_bounds,
)
from mcp_india_stack.tools.pan import validate_pan as _validate_pan
from mcp_india_stack.utils.responses import build_response


def _pan_fallback(val: Any, err: str) -> dict[str, Any]:
    """Fallback representation for failed or malformed PAN item."""
    pan_str = str(val) if val is not None else ""
    auth = create_pan_authenticity(pan=pan_str, valid=False)
    return {
        "valid": False,
        "pan": pan_str,
        "errors": [err],
        "warnings": [],
        "authenticity": auth,
    }


def _validate_single_pan(pan: str) -> dict[str, Any]:
    """Validate a single PAN with error isolation."""
    from mcp_india_stack import tools

    _fn = getattr(tools, "validate_pan", None) or _validate_pan
    try:
        if pan is None or not isinstance(pan, str):
            return _pan_fallback(
                pan, f"Invalid PAN format: expected string, got {type(pan).__name__}"
            )
        return _fn(pan)
    except Exception as exc:
        return _pan_fallback(pan, f"Validation error: {exc}")


def bulk_validate_pan(pans: list[str]) -> dict[str, Any]:
    """Validate multiple PANs in parallel using shared ThreadPoolExecutor.

    Args:
        pans: List of 10-character PAN strings.

    Returns:
        Standard envelope with per-PAN results and valid count.
    """
    is_valid, errors = validate_bulk_bounds(pans, entity_name="PAN")
    if not is_valid:
        return build_response(success=False, data=None, errors=errors)

    ordered_results = execute_bulk_items(
        items=pans,
        validate_fn=_validate_pan,
        fallback_fn=_pan_fallback,
        entity_name="PAN",
    )
    valid_count = sum(1 for r in ordered_results if r.get("valid"))
    summary = summarize_authenticity_levels(ordered_results)

    return build_response(
        success=True,
        data={
            "results": ordered_results,
            "total": len(pans),
            "valid_count": valid_count,
            "authenticity_summary": summary,
        },
        source="offline_algorithm",
        authenticity={"summary": summary},
    )
