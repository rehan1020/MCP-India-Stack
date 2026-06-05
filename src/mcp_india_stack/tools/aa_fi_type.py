"""AA FI Type decoder - maps FI types to descriptions and MCP tool pairings."""

from __future__ import annotations

from typing import Any

FI_TYPE_MAP: dict[str, dict[str, Any]] = {
    "DEPOSIT": {
        "description": "Bank savings/current/FD account data",
        "typical_fields": ["accountNumber", "ifsc", "currentBalance", "transactions"],
        "mcp_tool_pairing": "lookup_ifsc",
    },
    "MUTUAL_FUNDS": {
        "description": "Mutual fund folio and NAV data",
        "typical_fields": ["folioNumber", "schemeName", "units", "nav", "currentValue"],
        "mcp_tool_pairing": None,
    },
    "INSURANCE": {
        "description": "Life, health, and general insurance policy data",
        "typical_fields": ["policyNumber", "premiumAmount", "sumAssured", "maturityDate"],
        "mcp_tool_pairing": None,
    },
    "NPS": {
        "description": "National Pension System account data",
        "typical_fields": ["pran", "tier1Balance", "tier2Balance"],
        "mcp_tool_pairing": None,
    },
    "EQUITIES": {
        "description": "Stock portfolio and demat account data",
        "typical_fields": ["isin", "quantity", "averageCostPrice", "currentMarketValue"],
        "mcp_tool_pairing": "calculate_capital_gains",
    },
    "GSTIN_DATA": {
        "description": "GST return filing and liability data",
        "typical_fields": ["gstin", "filingStatus", "taxLiability"],
        "mcp_tool_pairing": "validate_gstin, calculate_gst",
    },
    "CREDIT_CARD": {
        "description": "Credit card statement and outstanding data",
        "typical_fields": ["maskedCardNumber", "outstandingBalance", "transactions"],
        "mcp_tool_pairing": None,
    },
    "RECURRING_DEPOSIT": {
        "description": "Recurring deposit account data",
        "typical_fields": ["accountNumber", "installmentAmount", "maturityDate", "maturityAmount"],
        "mcp_tool_pairing": None,
    },
}

DISCLAIMER = (
    "FI data schema is defined per ReBIT AA Tech Spec. "
    "Actual fields may vary by FIP implementation."
)


def decode_aa_fi_type(fi_type: str) -> dict[str, Any]:
    """Decode a Financial Information type from AA spec.

    Args:
        fi_type: FI type code (e.g., "DEPOSIT", "MUTUAL_FUNDS")

    Returns:
        Dict with description, typical fields, and MCP tool pairings.
    """
    fi_type_upper = fi_type.upper()

    if fi_type_upper not in FI_TYPE_MAP:
        return {
            "fi_type": fi_type,
            "description": None,
            "typical_fields": [],
            "mcp_tool_pairing": None,
            "error": f"Unknown FI type '{fi_type}'. Valid types: {list(FI_TYPE_MAP.keys())}",
            "disclaimer": DISCLAIMER,
        }

    info = FI_TYPE_MAP[fi_type_upper]

    return {
        "fi_type": fi_type_upper,
        "description": info["description"],
        "typical_fields": info["typical_fields"],
        "mcp_tool_pairing": info["mcp_tool_pairing"],
        "note": (
            "FI data schema is defined per ReBIT AA Tech Spec. "
            "Actual fields may vary by FIP implementation."
        ),
        "disclaimer": DISCLAIMER,
    }
