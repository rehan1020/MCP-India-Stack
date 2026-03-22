"""IFSC lookup and validation."""

from __future__ import annotations

import re
from typing import Any

import httpx

from mcp_india_stack.utils.loader import load_ifsc_index

IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def lookup_ifsc(code: str) -> dict[str, Any]:
    """Lookup IFSC from bundled dataset with Razorpay live API fallback."""
    if code is None:
        return {"found": False, "errors": ["IFSC code is required"]}

    value = str(code).strip().upper()
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("IFSC code cannot be empty")
    elif len(value) != 11:
        errors.append("IFSC code must be exactly 11 characters")
    elif not IFSC_RE.match(value):
        errors.append("IFSC must match format: 4 letters, 0, 6 alphanumeric")

    if errors:
        return {"found": False, "ifsc": value, "errors": errors, "warnings": warnings}

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
            "errors": errors,
            "warnings": warnings,
        }

    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"https://ifsc.razorpay.com/{value}")
        if response.status_code == 200:
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
                "errors": errors,
                "warnings": [
                    "IFSC was not present in bundled dataset and was resolved via live API"
                ],
            }
    except Exception:
        warnings.append("Live IFSC fallback failed or timed out")

    return {
        "found": False,
        "ifsc": value,
        "source": "bundled_dataset",
        "errors": ["IFSC not found in local dataset"],
        "warnings": warnings,
    }
