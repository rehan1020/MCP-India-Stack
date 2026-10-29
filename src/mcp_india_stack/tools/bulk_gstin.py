"""Bulk GSTIN validation using thread pool."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from mcp_india_stack.tools.bulk_common import BULK_WORKERS
from mcp_india_stack.tools.gstin import validate_gstin as core_validate_gstin
from mcp_india_stack.utils.responses import build_response


def _validate_single_gstin(gstin: str) -> dict[str, Any]:
    """Validate a single GSTIN with error isolation."""
    try:
        return core_validate_gstin(gstin)
    except Exception as exc:
        return {
            "valid": False,
            "gstin": gstin,
            "errors": [f"Validation error: {exc}"],
            "warnings": [],
            "live_verified": False,
            "verification_source": "offline",
        }


def bulk_validate_gstin(gstins: list[str]) -> dict[str, Any]:
    """Validate multiple GSTINs in parallel using ThreadPoolExecutor.

    Args:
        gstins: List of 15-character GSTIN strings.

    Returns:
        Standard envelope with per-GSTIN results, valid/invalid counts.
    """
    if not gstins:
        return build_response(
            success=False, data=None, errors=["Empty GSTIN list"], source="offline_algorithm"
        )
    if len(gstins) > 500:
        return build_response(
            success=False,
            data=None,
            errors=["Maximum 500 GSTINs per call"],
            source="offline_algorithm",
        )
    results: list[tuple[int, dict[str, Any]]] = []
    valid_count = 0
    invalid_count = 0
    with ThreadPoolExecutor(max_workers=BULK_WORKERS) as executor:
        future_to_index: dict[Any, int] = {
            executor.submit(_validate_single_gstin, gstin): idx for idx, gstin in enumerate(gstins)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            result = future.result()
            results.append((idx, result))
            if result.get("valid"):
                valid_count += 1
            else:
                invalid_count += 1
    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]
    return build_response(
        success=True,
        data={
            "results": ordered_results,
            "total": len(gstins),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        },
        source="offline_algorithm",
    )
