"""Shared test constants and expected thresholds."""

from __future__ import annotations

EXPECTED_TOOL_COUNT_ELEVATED_OFF: int = 74
EXPECTED_TOOL_COUNT_ELEVATED_ON: int = 78

SCHEMA_TOOLS: frozenset[str] = frozenset(
    {
        "validate_gstin",
        "validate_pan",
        "validate_upi_vpa",
        "validate_aadhaar",
        "validate_voter_id",
        "validate_driving_license",
        "validate_passport",
        "validate_cin",
        "validate_din",
        "bulk_validate_gstin",
        "calculate_income_tax",
        "calculate_tds",
        "calculate_gst",
        "calculate_surcharge",
        "calculate_hra_exemption",
        "calculate_capital_gains",
        "calculate_advance_tax",
        "lookup_pincode",
        "lookup_hsn_code",
        "decode_state_code",
        "lookup_ifsc",
    }
)
