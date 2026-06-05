"""HSN/SAC lookup and search logic."""

from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.loader import load_hsn_index, load_hsn_rows
from mcp_india_stack.utils.responses import build_response

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
            return build_response(
                success=False,
                data={"found": False},
                errors=["HSN/SAC code must be 2-8 digits"],
                source="offline_static",
            )

        rows = load_hsn_index().get(normalized)
        if not rows:
            return build_response(
                success=False,
                data={"found": False, "hsn_code": normalized},
                errors=["HSN/SAC code not found in bundled dataset"],
                source="offline_static",
            )

        row = rows[0]
        return build_response(
            success=True,
            data={
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
            },
            source="offline_static",
            validated_by=["db_lookup"],
        )

    if keyword:
        token = str(keyword).strip().lower()
        if not token:
            return build_response(
                success=False,
                data={"found": False},
                errors=["Keyword cannot be empty"],
                source="offline_static",
            )

        matches = [r for r in load_hsn_rows() if token in str(r.get("Description", "")).lower()]
        matches.sort(key=lambda r: len(str(r.get("Description", ""))))
        top = matches[:5]
        found = len(top) > 0
        errors = [] if top else ["No matching HSN/SAC description found"]
        return build_response(
            success=found,
            data={
                "found": found,
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
            },
            errors=errors,
            source="offline_static",
            validated_by=["db_lookup"],
        )

    return build_response(
        success=False,
        data={"found": False},
        errors=["Provide either code or keyword"],
        source="offline_static",
    )
