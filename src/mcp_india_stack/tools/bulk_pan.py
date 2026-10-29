"""Bulk PAN validation using thread pool."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from mcp_india_stack.tools.bulk_common import BULK_WORKERS
from mcp_india_stack.utils.responses import build_response


def _validate_single_pan(pan: str) -> dict[str, Any]:
    """Validate a single PAN with error isolation."""
    from mcp_india_stack.tools import validate_pan as _validate_pan

    try:
        return _validate_pan(pan)
    except Exception as exc:
        return {"valid": False, "pan": pan, "errors": [f"Validation error: {exc}"], "warnings": []}


def bulk_validate_pan(pans: list[str]) -> dict[str, Any]:
    """Validate multiple PANs in parallel using ThreadPoolExecutor.

    Args:
        pans: List of 10-character PAN strings.

    Returns:
        Standard envelope with per-PAN results and valid count.
    """
    if not pans:
        return build_response(success=False, data=None, errors=["Empty PAN list"])
    if len(pans) > 500:
        return build_response(success=False, data=None, errors=["Maximum 500 PANs per call"])

    results: list[tuple[int, dict[str, Any]]] = []
    valid_count = 0
    with ThreadPoolExecutor(max_workers=BULK_WORKERS) as executor:
        futures = {executor.submit(_validate_single_pan, pan): idx for idx, pan in enumerate(pans)}
        for future in as_completed(futures):
            result = future.result()
            results.append((futures[future], result))
            if result.get("valid"):
                valid_count += 1
    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]
    return build_response(
        success=True,
        data={"results": ordered_results, "total": len(pans), "valid_count": valid_count},
        source="offline_algorithm",
    )
