"""Standard response shapes for all tools."""

from __future__ import annotations

import os
from typing import Any

from mcp_india_stack import __version__

_LIVE_LOOKUP = os.environ.get("MCP_INDIA_STACK_LIVE_LOOKUP") == "1"


def build_response(
    *,
    success: bool,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    source: str = "offline_algorithm",
    normalized_input: str | None = None,
    confidence: float | None = None,
    validated_by: list[str] | None = None,
    stale: bool = False,
    stale_reason: str | None = None,
    data_version: str | None = None,
    rate_limit_remaining: int | None = None,
    rate_limit_warning: str | None = None,
) -> dict[str, Any]:
    """Build a normalized tool response envelope with confidence scoring."""

    # Determine confidence if not provided - use default based on success
    if confidence is None:
        if validated_by:
            confidence = _calculate_confidence(validated_by, success)
        elif success:
            confidence = 0.4  # Default to format-only confidence for successful responses
        else:
            confidence = 0.0

    # Default validated_by if not provided
    if validated_by is None:
        validated_by = ["format"] if success else []

    # Add any stale warnings
    response_warnings = list(warnings or [])
    if stale:
        response_warnings.append(
            f"Data may be stale: {stale_reason}" if stale_reason else "Data may be stale"
        )

    # Build response
    response = {
        "success": success,
        "data": data,
        "errors": errors or [],
        "warnings": response_warnings,
        "source": source,
        "tool_version": __version__,
    }

    # Add optional fields
    if normalized_input is not None:
        response["normalized_input"] = normalized_input
    response["confidence"] = confidence
    if validated_by:
        response["validated_by"] = validated_by
    if stale:
        response["stale"] = stale
        if stale_reason:
            response["stale_reason"] = stale_reason
    if data_version:
        response["data_version"] = data_version
    if rate_limit_remaining is not None:
        response["rate_limit_remaining"] = rate_limit_remaining
        if rate_limit_warning:
            response["rate_limit_warning"] = rate_limit_warning

    return response


def _calculate_confidence(validated_by: list[str], success: bool) -> float:
    """Calculate confidence score based on validation methods.

    Scoring guide:
    - Format only: 0.4
    - Format + checksum: 0.65
    - + live ping success: 0.85
    - + DB confirmed: 1.0
    """
    if not success:
        return 0.0

    base = 0.0

    if "format" in validated_by:
        base = 0.4
    if "checksum" in validated_by:
        base = max(base, 0.65)
    if "live_ping" in validated_by or "live_verified" in validated_by:
        base = max(base, 0.85)
    if "db_lookup" in validated_by or "db_verified" in validated_by:
        base = max(base, 1.0)

    return min(base, 1.0)
