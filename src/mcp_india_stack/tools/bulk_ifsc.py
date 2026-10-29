"""Bulk IFSC validation using thread pool."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from mcp_india_stack.tools.bulk_common import BULK_WORKERS
from mcp_india_stack.utils.responses import build_response


def _validate_single_ifsc(ifsc: str) -> dict[str, Any]:
    """Validate a single IFSC with error isolation."""
    from mcp_india_stack.tools import lookup_ifsc as _lookup_ifsc

    try:
        return _lookup_ifsc(ifsc)
    except Exception as exc:
        return {"found": False, "ifsc": ifsc, "errors": [f"Lookup error: {exc}"], "warnings": []}


def bulk_validate_ifsc(ifscs: list[str]) -> dict[str, Any]:
    """Validate multiple IFSC codes in parallel using ThreadPoolExecutor.

    Args:
        ifscs: List of 11-character IFSC code strings.

    Returns:
        Standard envelope with per-IFSC results and found count.
    """
    if not ifscs:
        return build_response(success=False, data=None, errors=["Empty IFSC list"])
    if len(ifscs) > 500:
        return build_response(success=False, data=None, errors=["Maximum 500 IFSCs per call"])
    results: list[tuple[int, dict[str, Any]]] = []
    found_count = 0
    with ThreadPoolExecutor(max_workers=BULK_WORKERS) as executor:
        futures = {
            executor.submit(_validate_single_ifsc, ifsc): idx for idx, ifsc in enumerate(ifscs)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append((futures[future], result))
            if result.get("found"):
                found_count += 1
    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]
    return build_response(
        success=True,
        data={"results": ordered_results, "total": len(ifscs), "found_count": found_count},
        source="offline_algorithm",
    )
