"""HSN/SAC lookup and search logic."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.loader import load_hsn_index, load_hsn_rows

CODE_RE = re.compile(r"^[0-9]{2,8}$")

DISCLAIMER = (
    "GST rates may vary based on specific conditions. Verify with a tax professional "
    "for commercial transactions."
)


def _category(code: str) -> str:
    return "services" if code.startswith("99") else "goods"


def lookup_hsn_code(code: str | None = None, keyword: str | None = None) -> dict[str, Any]:
    """Lookup exact HSN/SAC code or search descriptions by keyword."""
    if code:
        normalized = str(code).strip()
        if not CODE_RE.match(normalized):
            return {
                "found": False,
                "errors": ["HSN/SAC code must be 2-8 digits"],
                "warnings": [],
            }

        rows = load_hsn_index().get(normalized)
        if not rows:
            return {
                "found": False,
                "hsn_code": normalized,
                "errors": ["HSN/SAC code not found in bundled dataset"],
                "warnings": [],
            }

        row = rows[0]
        return {
            "found": True,
            "hsn_code": normalized,
            "description": row.get("Description"),
            "cgst_rate": row.get("CGST_Rate"),
            "sgst_rate": row.get("SGST_Rate"),
            "igst_rate": row.get("IGST_Rate"),
            "cess_rate": row.get("CESS_Rate"),
            "category": _category(normalized),
            "hierarchy_level": len(normalized),
            "disclaimer": DISCLAIMER,
            "errors": [],
            "warnings": [],
        }

    if keyword:
        token = str(keyword).strip().lower()
        if not token:
            return {
                "found": False,
                "errors": ["Keyword cannot be empty"],
                "warnings": [],
            }

        matches = [r for r in load_hsn_rows() if token in str(r.get("Description", "")).lower()]
        matches.sort(key=lambda r: len(str(r.get("Description", ""))))
        top = matches[:5]
        return {
            "found": len(top) > 0,
            "query": token,
            "results": [
                {
                    "hsn_code": str(r.get("HSNCode")),
                    "description": r.get("Description"),
                    "igst_rate": r.get("IGST_Rate"),
                    "category": _category(str(r.get("HSNCode"))),
                    "hierarchy_level": len(str(r.get("HSNCode"))),
                }
                for r in top
            ],
            "disclaimer": DISCLAIMER,
            "errors": [] if top else ["No matching HSN/SAC description found"],
            "warnings": [],
        }

    return {
        "found": False,
        "errors": ["Provide either code or keyword"],
        "warnings": [],
    }
