"""IFSC lookup and validation."""

from __future__ import annotations

import os
import re
import threading
import time
from typing import Any

import httpx

from mcp_india_stack.utils.loader import load_ifsc_index

IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

_LIVE_LOOKUP_ENABLED = os.environ.get("MCP_INDIA_STACK_LIVE_LOOKUP") == "1"

# Circuit breaker constants (internal resilience guard — not env-configurable)
_CB_FAILURE_THRESHOLD = 5  # consecutive failures to trip the breaker
_CB_COOLDOWN_SECONDS = 30  # seconds to wait before retrying after trip


class _CircuitBreaker:
    """Process-global, thread-safe circuit breaker for live IFSC lookups."""

    def __init__(self, threshold: int, cooldown: float) -> None:
        self._threshold = threshold
        self._cooldown = cooldown
        self._consecutive_failures = 0
        self._open_until: float = 0.0
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            if self._consecutive_failures >= self._threshold:
                return time.monotonic() < self._open_until
            return False

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._threshold:
                self._open_until = time.monotonic() + self._cooldown


_ifsc_breaker = _CircuitBreaker(_CB_FAILURE_THRESHOLD, _CB_COOLDOWN_SECONDS)


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def lookup_ifsc(code: str) -> dict[str, Any]:
    """Lookup IFSC from bundled dataset with optional live API fallback.

    Args:
        code: IFSC code to lookup.

    Returns:
        Dict with found flag, branch details, payment rails, source,
        live_verified flag, and verification_source.
    """
    from mcp_india_stack.normalization import normalize_ifsc

    if code is None:
        return {"found": False, "errors": ["IFSC code is required"]}

    normalized = normalize_ifsc(code)
    value = normalized["normalized_input"]
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("IFSC code cannot be empty")
    elif len(value) != 11:
        errors.append("IFSC code must be exactly 11 characters")
    elif not IFSC_RE.match(value):
        errors.append("IFSC must match format: 4 letters, 0, 6 alphanumeric")

    if errors:
        return {
            "found": False,
            "ifsc": value,
            "errors": errors,
            "warnings": warnings,
            "live_verified": False,
            "verification_source": "offline",
        }

    row = load_ifsc_index().get(value)
    if row:
        return {
            "found": True,
            "ifsc": value,
            "bank": row.get("BANK"),
            "branch": row.get("BRANCH"),
            "address": row.get("ADDRESS"),
            "city": row.get("CITY"),
            "district": row.get("DISTRICT"),
            "state": row.get("STATE"),
            "micr": row.get("MICR"),
            "upi_enabled": _to_bool(row.get("UPI")),
            "rtgs_enabled": _to_bool(row.get("RTGS")),
            "neft_enabled": _to_bool(row.get("NEFT")),
            "imps_enabled": _to_bool(row.get("IMPS")),
            "swift": row.get("SWIFT"),
            "source": "bundled_dataset",
            "live_verified": False,
            "verification_source": "offline",
            "errors": errors,
            "warnings": warnings,
        }

    if _LIVE_LOOKUP_ENABLED:
        if _ifsc_breaker.is_open:
            warnings.append("live_lookup_skipped: circuit_open")
        else:
            try:
                with httpx.Client(timeout=3.0) as client:
                    response = client.get(f"https://ifsc.razorpay.com/{value}")
                if response.status_code == 200:
                    _ifsc_breaker.record_success()
                    payload = response.json()
                    return {
                        "found": True,
                        "ifsc": value,
                        "bank": payload.get("BANK"),
                        "branch": payload.get("BRANCH"),
                        "address": payload.get("ADDRESS"),
                        "city": payload.get("CITY"),
                        "district": payload.get("DISTRICT"),
                        "state": payload.get("STATE"),
                        "micr": payload.get("MICR"),
                        "upi_enabled": _to_bool(payload.get("UPI")),
                        "rtgs_enabled": _to_bool(payload.get("RTGS")),
                        "neft_enabled": _to_bool(payload.get("NEFT")),
                        "imps_enabled": _to_bool(payload.get("IMPS")),
                        "swift": payload.get("SWIFT"),
                        "source": "live_api",
                        "live_verified": True,
                        "verification_source": "live",
                        "errors": errors,
                        "warnings": warnings,
                    }
                else:
                    _ifsc_breaker.record_failure()
                    warnings.append(f"Live IFSC API returned {response.status_code}")
            except Exception:
                _ifsc_breaker.record_failure()
                warnings.append("Live IFSC fallback failed or timed out")

    return {
        "found": False,
        "ifsc": value,
        "source": "bundled_dataset",
        "live_verified": False,
        "verification_source": "offline" if not _LIVE_LOOKUP_ENABLED else "live",
        "errors": ["IFSC not found in local dataset"],
        "warnings": warnings,
    }
