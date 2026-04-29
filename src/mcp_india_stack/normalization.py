"""Input normalization layer for MCP India Stack.

Normalizes messy agent input before validation:
- Strip leading/trailing whitespace
- Collapse internal spaces
- Uppercase alphabetic characters
- Remove hyphens and dots where not structurally meaningful

Applies to: GSTIN, PAN, IFSC, Aadhaar, CIN, FSSAI, UPI VPA, pincode
"""

from __future__ import annotations

import re
from typing import Any


def normalize_input(value: str, input_type: str) -> dict[str, Any]:
    """Normalize input based on type.

    Args:
        value: Raw input string
        input_type: Type of input (gstin, pan, ifsc, aadhaar, cin, fssai, upi, pincode)

    Returns:
        Dict with normalized_input and original_input
    """
    if not value:
        return {"original_input": "", "normalized_input": "", "warnings": []}

    original = value
    normalized = value.strip()
    warnings = []

    # Collapse internal spaces
    normalized = re.sub(r"\s+", "", normalized)

    if input_type in ("gstin", "pan", "cin", "fssai", "ifsc"):
        # Uppercase for these types
        normalized = normalized.upper()
        # Remove hyphens and dots for continuous string format
        normalized = normalized.replace("-", "").replace(".", "")
    elif input_type == "aadhaar":
        # Aadhaar: keep only digits
        normalized = re.sub(r"[^0-9]", "", normalized)
    elif input_type == "upi":
        # UPI: lowercase the handle, keep @ symbol
        normalized = normalized.lower()
    elif input_type == "pincode":
        # Pincode: keep only digits
        normalized = re.sub(r"[^0-9]", "", normalized)

    # Warn if normalization made significant changes
    if original != normalized:
        warnings.append(f"Input normalized: '{original}' -> '{normalized}'")

    return {
        "original_input": original,
        "normalized_input": normalized,
        "warnings": warnings,
    }


def normalize_gstin(gstin: str) -> dict[str, Any]:
    """Normalize GSTIN input."""
    return normalize_input(gstin, "gstin")


def normalize_pan(pan: str) -> dict[str, Any]:
    """Normalize PAN input."""
    return normalize_input(pan, "pan")


def normalize_ifsc(ifsc: str) -> dict[str, Any]:
    """Normalize IFSC input."""
    return normalize_input(ifsc, "ifsc")


def normalize_aadhaar(aadhaar: str) -> dict[str, Any]:
    """Normalize Aadhaar input."""
    return normalize_input(aadhaar, "aadhaar")


def normalize_cin(cin: str) -> dict[str, Any]:
    """Normalize CIN input."""
    return normalize_input(cin, "cin")


def normalize_fssai(fssai: str) -> dict[str, Any]:
    """Normalize FSSAI input."""
    return normalize_input(fssai, "fssai")


def normalize_upi(vpa: str) -> dict[str, Any]:
    """Normalize UPI VPA input."""
    return normalize_input(vpa, "upi")


def normalize_pincode(pincode: str) -> dict[str, Any]:
    """Normalize pincode input."""
    return normalize_input(pincode, "pincode")
