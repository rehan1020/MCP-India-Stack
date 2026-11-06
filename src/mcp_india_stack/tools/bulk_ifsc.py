"""Bulk IFSC validation using shared bounded executor."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.authenticity.models import summarize_authenticity_levels
from mcp_india_stack.authenticity.rules import create_ifsc_authenticity
from mcp_india_stack.tools.bulk_common import (
    execute_bulk_items,
    validate_bulk_bounds,
)
from mcp_india_stack.tools.ifsc import lookup_ifsc as _lookup_ifsc
from mcp_india_stack.utils.responses import build_response


def _ifsc_fallback(val: Any, err: str) -> dict[str, Any]:
    """Fallback representation for failed or malformed IFSC item."""
    ifsc_str = str(val) if val is not None else ""
    auth = create_ifsc_authenticity(ifsc=ifsc_str, found=False)
    return {
        "found": False,
        "ifsc": ifsc_str,
        "errors": [err],
        "warnings": [],
        "authenticity": auth,
    }


def _validate_single_ifsc(ifsc: str) -> dict[str, Any]:
    """Validate a single IFSC with error isolation."""
    from mcp_india_stack import tools

    _fn = getattr(tools, "lookup_ifsc", None) or _lookup_ifsc
    try:
        if ifsc is None or not isinstance(ifsc, str):
            return _ifsc_fallback(
                ifsc, f"Invalid IFSC format: expected string, got {type(ifsc).__name__}"
            )
        return _fn(ifsc)
    except Exception as exc:
        return _ifsc_fallback(ifsc, f"Lookup error: {exc}")


def bulk_validate_ifsc(ifscs: list[str]) -> dict[str, Any]:
    """Validate multiple IFSC codes in parallel using shared ThreadPoolExecutor.

    Args:
        ifscs: List of 11-character IFSC code strings.

    Returns:
        Standard envelope with per-IFSC results and found count.
    """
    is_valid, errors = validate_bulk_bounds(ifscs, entity_name="IFSC")
    if not is_valid:
        return build_response(success=False, data=None, errors=errors)

    ordered_results = execute_bulk_items(
        items=ifscs,
        validate_fn=_lookup_ifsc,
        fallback_fn=_ifsc_fallback,
        entity_name="IFSC",
    )
    found_count = sum(1 for r in ordered_results if r.get("found"))
    summary = summarize_authenticity_levels(ordered_results)

    return build_response(
        success=True,
        data={
            "results": ordered_results,
            "total": len(ifscs),
            "found_count": found_count,
            "authenticity_summary": summary,
        },
        source="offline_algorithm",
        authenticity={"summary": summary},
    )
