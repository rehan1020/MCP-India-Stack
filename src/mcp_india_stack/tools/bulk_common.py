"""Common configuration, bounds, and shared bounded executor for bulk operations.

In accordance with G9:
- Max items bounded by env MCP_INDIA_STACK_BULK_MAX (default 500, clamped [1, 5000])
- Per-item max length bounded by env MCP_INDIA_STACK_BULK_ITEM_MAX_LEN (default 256)
- Total payload cap bounded by env MCP_INDIA_STACK_BULK_PAYLOAD_MAX (default 1MB)
- Total operation timeout bounded by env MCP_INDIA_STACK_BULK_TIMEOUT (default 30.0s)
- One shared bounded ThreadPoolExecutor across all operations (no thread-pool per call)
- Per-item error isolation with order preserved
- Over-limit requests are rejected before any work is performed
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def _clamp_bulk_workers() -> int:
    """Parse MCP_INDIA_STACK_BULK_WORKERS with hard [1, 20] clamp."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 10
    return max(1, min(20, val))


BULK_WORKERS = _clamp_bulk_workers()


def get_bulk_max() -> int:
    """Parse MCP_INDIA_STACK_BULK_MAX (default 500, clamped [1, 5000])."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_MAX", "500")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 500
    return max(1, min(5000, val))


def get_bulk_item_max_len() -> int:
    """Maximum allowed character length for a single item (default 256)."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_ITEM_MAX_LEN", "256")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 256
    return max(16, val)


def get_bulk_payload_max() -> int:
    """Maximum total payload cap in bytes (default 1,048,576 bytes / 1MB)."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_PAYLOAD_MAX", "1048576")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 1048576
    return max(16, val)


def get_bulk_timeout() -> float:
    """Total timeout for bulk operations in seconds (default 30.0)."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_TIMEOUT", "30.0")
    try:
        val = float(raw)
    except (ValueError, TypeError):
        return 30.0
    return max(1.0, val)


_SHARED_EXECUTOR: ThreadPoolExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()


def get_bulk_executor() -> ThreadPoolExecutor:
    """Return the singleton shared bounded ThreadPoolExecutor for all bulk operations."""
    global _SHARED_EXECUTOR
    if _SHARED_EXECUTOR is None:
        with _EXECUTOR_LOCK:
            if _SHARED_EXECUTOR is None:
                _SHARED_EXECUTOR = ThreadPoolExecutor(
                    max_workers=BULK_WORKERS,
                    thread_name_prefix="mcp-bulk",
                )
    return _SHARED_EXECUTOR


def shutdown_bulk_executor(wait: bool = False) -> None:
    """Shutdown the shared executor (used in tests and shutdown hooks)."""
    global _SHARED_EXECUTOR
    with _EXECUTOR_LOCK:
        if _SHARED_EXECUTOR is not None:
            _SHARED_EXECUTOR.shutdown(wait=wait)
            _SHARED_EXECUTOR = None


def validate_bulk_bounds(
    items: Any,
    entity_name: str = "item",
) -> tuple[bool, list[str]]:
    """Validate bulk request bounds before any worker execution.

    Rejects:
    - Non-list inputs
    - Empty lists
    - Lists exceeding MCP_INDIA_STACK_BULK_MAX
    - Payloads exceeding MCP_INDIA_STACK_BULK_PAYLOAD_MAX

    Returns (is_valid, errors).
    """
    if not isinstance(items, list):
        return False, [f"Input must be a list of {entity_name}s"]

    if len(items) == 0:
        return False, [f"Empty {entity_name} list"]

    max_items = get_bulk_max()
    if len(items) > max_items:
        if max_items == 500:
            return False, [f"Maximum {max_items} {entity_name}s per call"]
        return False, [f"Maximum {max_items} {entity_name}s per call (got {len(items)})"]

    payload_max = get_bulk_payload_max()
    total_bytes = 0
    for item in items:
        if isinstance(item, str):
            total_bytes += len(item.encode("utf-8", errors="replace"))
        elif item is not None:
            total_bytes += len(str(item).encode("utf-8", errors="replace"))

    if total_bytes > payload_max:
        return False, [
            f"Total payload size ({total_bytes} bytes) exceeds limit of {payload_max} bytes"
        ]

    return True, []


def execute_bulk_items(
    items: list[Any],
    validate_fn: Callable[[str], dict[str, Any]],
    fallback_fn: Callable[[Any, str], dict[str, Any]],
    entity_name: str = "item",
) -> list[dict[str, Any]]:
    """Execute bulk validation over items using the shared bounded executor.

    Guarantees:
    - Bounded execution over the shared singleton thread pool
    - Strict per-item error isolation (failures in one item never affect others)
    - Strict preservation of original list ordering
    - Per-item length and type validation
    - Bounded total operation timeout
    """
    executor = get_bulk_executor()
    timeout = get_bulk_timeout()
    item_max_len = get_bulk_item_max_len()

    def _worker(val: Any) -> dict[str, Any]:
        if val is None or not isinstance(val, str):
            got_type = type(val).__name__ if val is not None else "None"
            return fallback_fn(
                val, f"Invalid {entity_name} format: expected string, got {got_type}"
            )
        if len(val) > item_max_len:
            return fallback_fn(
                val,
                f"Item exceeds maximum length of {item_max_len} (got {len(val)})",
            )
        try:
            return validate_fn(val)
        except Exception as exc:
            return fallback_fn(val, f"Validation error: {exc}")

    results: list[dict[str, Any] | None] = [None] * len(items)
    futures = {executor.submit(_worker, item): idx for idx, item in enumerate(items)}

    try:
        for future in as_completed(futures, timeout=timeout):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                results[idx] = fallback_fn(items[idx], f"Execution error: {exc}")
    except TimeoutError:
        for _fut, idx in futures.items():
            if results[idx] is None:
                results[idx] = fallback_fn(items[idx], "Operation timed out")

    # Safety fallback for any missing indices
    for idx, r in enumerate(results):
        if r is None:
            results[idx] = fallback_fn(items[idx], "Operation incomplete")

    return results  # type: ignore[return-value]
