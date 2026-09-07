from __future__ import annotations

import re
from typing import Any

from mcp_india_stack.utils.responses import build_response


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    """Hoist data keys to top-level for backwards compatibility."""
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


# eCourts CNR state prefixes → state names (alphabetic, NOT GST numeric)
_CNR_STATE_MAP: dict[str, str] = {
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CG": "Chhattisgarh",
    "CH": "Chandigarh",
    "DL": "Delhi",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HP": "Himachal Pradesh",
    "HR": "Haryana",
    "JH": "Jharkhand",
    "JK": "Jammu and Kashmir",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "MH": "Maharashtra",
    "ML": "Meghalaya",
    "MN": "Manipur",
    "MP": "Madhya Pradesh",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "PB": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TR": "Tripura",
    "TS": "Telangana",
    "UK": "Uttarakhand",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
    "AN": "Andaman and Nicobar Islands",
    "DD": "Dadra and Nagar Haveli and Daman and Diu",
    "DN": "Dadra and Nagar Haveli and Daman and Diu",
    "LD": "Lakshadweep",
    "PY": "Puducherry",
}


def decode_cnr_number(cnr: str) -> dict[str, Any]:
    """
    Decode an Indian Court Case Number Record (CNR).

    Input:
    - cnr (str): The 16-character CNR number.

    Output: cnr, state_code, state_name, court_establishment_code,
    sequence_number, filing_year, is_structurally_valid, success

    Example prompt: "Decode CNR number DLCT010012342024"

    Limitations: Structural validation only, does not verify
    existence in court databases.
    """
    errors: list[str] = []
    warnings: list[str] = []

    cnr_clean = str(cnr).strip().replace("-", "").replace(" ", "").upper()
    is_structurally_valid = True

    if len(cnr_clean) != 16:
        is_structurally_valid = False
        errors.append(f"CNR must be exactly 16 characters. Got {len(cnr_clean)} characters.")

    pat = r"^[A-Z]{4}[0-9]{8}[0-9]{4}$"
    if len(cnr_clean) == 16 and not re.match(pat, cnr_clean):
        is_structurally_valid = False
        warnings.append("CNR format usually follows SSCC NNNNNNNN YYYY pattern.")

    state_code = cnr_clean[0:2] if len(cnr_clean) >= 2 else ""
    court_code = cnr_clean[0:4] if len(cnr_clean) >= 4 else ""
    seq = cnr_clean[4:12] if len(cnr_clean) >= 12 else ""
    year = cnr_clean[12:16] if len(cnr_clean) == 16 else ""

    state_name = _CNR_STATE_MAP.get(state_code, "")
    if not state_name and state_code:
        warnings.append(f"State code {state_code} not recognized.")

    data = {
        "cnr": cnr_clean,
        "state_code": state_code,
        "state_name": state_name,
        "court_establishment_code": court_code,
        "sequence_number": seq,
        "filing_year": year,
        "is_structurally_valid": is_structurally_valid,
    }

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data=data,
            errors=errors,
            warnings=warnings,
        )
    )
