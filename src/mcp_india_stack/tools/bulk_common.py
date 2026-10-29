"""Common configuration and worker limits for bulk operations."""

from __future__ import annotations

import os


def _clamp_bulk_workers() -> int:
    """Parse MCP_INDIA_STACK_BULK_WORKERS with hard [1, 20] clamp."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 10
    return max(1, min(20, val))


BULK_WORKERS = _clamp_bulk_workers()
