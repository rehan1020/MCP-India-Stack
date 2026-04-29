"""Structured telemetry for MCP India Stack.

PII-safe logging of tool usage for analytics and debugging.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

_ENABLED = os.environ.get("MCP_INDIA_STACK_LOG") == "1"
_LOG_PATH = os.environ.get("MCP_INDIA_STACK_LOG_PATH", "./telemetry.jsonl")


def _hash_input(input_value: str | None) -> str:
    """Hash input using SHA256, returning first 12 chars."""
    if not input_value:
        return ""
    sha = hashlib.sha256(input_value.encode()).hexdigest()
    return sha[:12]


def log_tool_usage(
    tool_name: str,
    input_value: str | None,
    latency_ms: float,
    result_type: str,
) -> None:
    """Log tool usage to telemetry file.

    Args:
        tool_name: Name of the tool called.
        input_value: The input provided (will be hashed).
        latency_ms: Execution time in milliseconds.
        result_type: 'valid', 'invalid', 'error', 'success', 'found', or 'not_found'.
    """
    if not _ENABLED:
        return

    try:
        hashed_input = _hash_input(input_value)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "hashed_input": hashed_input,
            "latency_ms": round(latency_ms, 2),
            "result_type": result_type,
        }

        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass


def get_telemetry_status() -> dict[str, Any]:
    """Get current telemetry configuration."""
    return {
        "enabled": _ENABLED,
        "log_path": _LOG_PATH,
        "pii_protection": "sha256(input)[:12]",
    }
