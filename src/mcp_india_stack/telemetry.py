"""Structured telemetry for MCP India Stack.

Pseudonymized logging of tool usage for analytics and debugging.
Pseudonymization guarantees are contingent on the pepper remaining secret.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

# Only enable telemetry if the pepper is set. Do not fall back to unsalted or raw logging.
_PEPPER = os.environ.get("MCP_INDIA_STACK_TELEMETRY_PEPPER", "")
_ENABLED = bool(_PEPPER)

_LOG_PATH = os.environ.get("MCP_INDIA_STACK_LOG_PATH", "./telemetry.jsonl")

# Configure a dedicated logger with a RotatingFileHandler (10MB max, 5 backups)
_telemetry_logger = logging.getLogger("mcp_india_stack.telemetry_sink")
_telemetry_logger.setLevel(logging.INFO)
_telemetry_logger.propagate = False  # Don't pass to root logger

if _ENABLED:
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(_LOG_PATH)), exist_ok=True)
        _handler = RotatingFileHandler(
            _LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        _handler.setFormatter(logging.Formatter("%(message)s"))
        _telemetry_logger.addHandler(_handler)
    except Exception as e:
        # If we can't create the log file, disable telemetry safely
        logging.getLogger(__name__).error(f"Failed to initialize telemetry logger: {e}")
        _ENABLED = False
else:
    logging.getLogger(__name__).info(
        "Telemetry disabled: MCP_INDIA_STACK_TELEMETRY_PEPPER is not set."
    )


def _hash_input(input_value: str | None) -> str:
    """Hash input using HMAC-SHA256 with the configured pepper."""
    if not input_value or not _ENABLED:
        return ""

    digest = hmac.new(
        key=_PEPPER.encode("utf-8"), msg=input_value.encode("utf-8"), digestmod="sha256"
    ).hexdigest()

    return digest[:16]  # Return 16 chars for pseudonymized identifier


def log_tool_usage(
    tool_name: str,
    input_value: str | None,
    latency_ms: float,
    result_type: str,
) -> None:
    """Log tool usage to telemetry file.

    Args:
        tool_name: Name of the tool called.
        input_value: The input provided (will be hashed with HMAC-SHA256).
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

        _telemetry_logger.info(json.dumps(log_entry))
    except Exception:
        pass


def get_telemetry_status() -> dict[str, Any]:
    """Get current telemetry configuration."""
    return {
        "enabled": _ENABLED,
        "log_path": _LOG_PATH,
        "pii_protection": "hmac-sha256(pepper, input)[:16]",
    }
