"""Bulk Aadhaar validation using thread pool."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from mcp_india_stack.tools.aadhaar import validate_aadhaar as core_validate_aadhaar

BULK_WORKERS = int(os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10"))

MAX_AADHAAR_BULK = 500

DISCLAIMER = "Structural and Verhoeff checksum validation only. Not connected to UIDAI."


def _validate_single_aadhaar(aadhaar: str) -> dict[str, Any]:
    """Validate a single Aadhaar with error isolation."""
    try:
        result = core_validate_aadhaar(aadhaar)
        return {
            "masked": result.get("masked", ""),
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
        }
    except Exception as exc:
        return {
            "masked": "",
            "valid": False,
            "errors": [f"Validation error: {exc}"],
        }


def bulk_validate_aadhaar(numbers: list[str]) -> dict[str, Any]:
    """Validate multiple Aadhaar numbers in parallel using ThreadPoolExecutor.

    Args:
        numbers: List of Aadhaar numbers (with or without spaces/hyphens).

    Returns:
        Dict with per-Aadhaar results and valid/invalid counts.
    """
    try:
        errors: list[str] = []

        if not numbers:
            errors.append("Empty Aadhaar list")

        if len(numbers) > MAX_AADHAAR_BULK:
            errors.append(f"Maximum {MAX_AADHAAR_BULK} Aadhaars per call")

        if errors:
            return {
                "total": len(numbers) if numbers else 0,
                "valid_count": 0,
                "invalid_count": 0,
                "results": [],
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        results: list[tuple[int, dict[str, Any]]] = []
        valid_count = 0
        invalid_count = 0

        with ThreadPoolExecutor(max_workers=BULK_WORKERS) as executor:
            future_to_index: dict[Any, int] = {
                executor.submit(_validate_single_aadhaar, aadhaar): idx
                for idx, aadhaar in enumerate(numbers)
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
        ordered_results = [{"index": idx, **r} for idx, r in results]

        return {
            "total": len(numbers),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "results": ordered_results,
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        return {
            "total": len(numbers) if numbers else 0,
            "valid_count": 0,
            "invalid_count": 0,
            "results": [],
            "errors": [f"Bulk validation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
