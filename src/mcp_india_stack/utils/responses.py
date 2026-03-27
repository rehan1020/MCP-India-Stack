"""Standard response shapes for all tools."""

from __future__ import annotations

from typing import Any

from mcp_india_stack import __version__


def build_response(
    *,
    success: bool,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    source: str = "offline_algorithm",
) -> dict[str, Any]:
    """Build a normalized tool response envelope."""
    return {
        "success": success,
        "data": data,
        "errors": errors or [],
        "warnings": warnings or [],
        "source": source,
        "tool_version": __version__,
    }
