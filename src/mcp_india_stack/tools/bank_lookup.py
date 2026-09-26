"""Bank lookup from bundled RBI master data (sample)."""

from __future__ import annotations

from typing import Any

# Bundled bank master data (sample)
_BANKS: list[dict[str, Any]] = [
    {
        "name": "State Bank of India",
        "code": "SBIN",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "HDFC Bank Limited",
        "code": "HDFC",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "ICICI Bank Limited",
        "code": "ICICI",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "Punjab National Bank",
        "code": "PNB",
        "type": "commercial",
        "hq": "New Delhi",
        "rbi_licensed": True,
    },
    {
        "name": "Bank of Baroda",
        "code": "BARODA",
        "type": "commercial",
        "hq": "Vadodara",
        "rbi_licensed": True,
    },
    {
        "name": "Canara Bank",
        "code": "CANARA",
        "type": "commercial",
        "hq": "Bengaluru",
        "rbi_licensed": True,
    },
    {
        "name": "Axis Bank Limited",
        "code": "AXIS",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "Kotak Mahindra Bank",
        "code": "KOTAK",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "Yes Bank Limited",
        "code": "YES",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
    {
        "name": "IDBI Bank Limited",
        "code": "IDBI",
        "type": "commercial",
        "hq": "Mumbai",
        "rbi_licensed": True,
    },
]


def lookup_bank(name_or_code: str) -> dict[str, Any]:
    """Look up bank details from RBI master list.

    Args:
        name_or_code: Bank name or IFSC code prefix to search.

    Returns:
        Dict with matched banks and count.
    """
    search = name_or_code.upper().strip()
    matches = [b for b in _BANKS if search in b["name"].upper() or search in b["code"]]
    return {"banks": matches, "count": len(matches), "found": len(matches) > 0}
