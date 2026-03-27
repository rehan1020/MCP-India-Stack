"""UPI VPA validation and handle decoding."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.loader import load_upi_handles

UPI_RE = re.compile(r"^[A-Za-z0-9._-]{3,256}@[A-Za-z0-9.-]{2,100}$")
INVALID_DOT_RE = re.compile(r"(^\.|\.$|\.\.)")


def validate_upi_vpa(vpa: str) -> dict[str, Any]:
    """Validate a UPI VPA and detect known provider handles."""
    if vpa is None:
        return {"valid": False, "errors": ["UPI VPA is required"]}

    value = str(vpa).strip()
    errors: list[str] = []
    warnings: list[str] = []

    if not value:
        errors.append("UPI VPA cannot be empty")
    elif not UPI_RE.match(value):
        errors.append("UPI VPA must match username@handle format")

    if errors:
        return {"valid": False, "vpa": value, "errors": errors, "warnings": warnings}

    username, handle = value.split("@", 1)
    username_norm = username.lower()
    handle_norm = handle.lower()

    if INVALID_DOT_RE.search(username_norm):
        errors.append("UPI username cannot start/end with '.' or contain consecutive dots")

    if errors:
        return {"valid": False, "vpa": value, "errors": errors, "warnings": warnings}

    mapping = load_upi_handles()
    provider = mapping.get(handle_norm)
    known_provider = provider is not None
    if not known_provider:
        warnings.append(
            "UPI handle is not in curated list; it may still be valid if recently onboarded"
        )

    return {
        "valid": True,
        "vpa": f"{username_norm}@{handle_norm}",
        "username": username_norm,
        "handle": handle_norm,
        "known_provider": known_provider,
        "provider_name": provider["provider_name"] if provider else None,
        "provider_type": provider["provider_type"] if provider else None,
        "errors": errors,
        "warnings": warnings,
    }
