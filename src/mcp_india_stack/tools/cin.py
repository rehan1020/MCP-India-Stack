"""CIN (Company Identification Number) validation and field decoding."""

from __future__ import annotations

import re
from typing import Any

# CIN format: L 21010 MH 1995 PLC 084717
# Pos:        1 2-6   7-8 9-12 13-15 16-21
CIN_RE = re.compile(r"^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$")

COMPANY_TYPES: dict[str, str] = {
    "PLC": "Public Limited Company",
    "PTC": "Private Limited Company",
    "FLC": "Foreign Company",
    "GOI": "Government Company",
    "NPL": "Not for Profit License Company",
    "OPC": "One Person Company",
    "ULC": "Unlimited Liability Company",
}

# Two-letter state codes used in CIN (same as GST state abbreviations)
CIN_STATE_CODES: dict[str, str] = {
    "AN": "Andaman and Nicobar Islands",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CH": "Chandigarh",
    "CG": "Chhattisgarh",
    "DD": "Dadra and Nagar Haveli and Daman and Diu",
    "DL": "Delhi",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "JK": "Jammu and Kashmir",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "LD": "Lakshadweep",
    "MH": "Maharashtra",
    "ML": "Meghalaya",
    "MN": "Manipur",
    "MP": "Madhya Pradesh",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "OR": "Odisha",
    "PB": "Punjab",
    "PY": "Puducherry",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TR": "Tripura",
    "UK": "Uttarakhand",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
}


def validate_cin(cin: str) -> dict[str, Any]:
    """Validate and decode an Indian CIN (Company Identification Number).

    CIN is 21 characters: [L/U][NIC 5-digit][State 2-letter][Year 4-digit]
    [Company type 3-letter][Serial 6-digit].

    Args:
        cin: CIN string to validate.

    Returns:
        Dict with decoded fields and validation status.
    """
    try:
        if cin is None:
            return {
                "valid": False,
                "cin": "",
                "listing_status": "",
                "nic_code": "",
                "state_code": "",
                "state_name": "",
                "year_of_incorporation": "",
                "company_type_code": "",
                "company_type": "",
                "sequential_number": "",
                "errors": ["CIN is required"],
            }

        cleaned = str(cin).strip().upper()
        errors: list[str] = []

        if not cleaned:
            return {
                "valid": False,
                "cin": "",
                "listing_status": "",
                "nic_code": "",
                "state_code": "",
                "state_name": "",
                "year_of_incorporation": "",
                "company_type_code": "",
                "company_type": "",
                "sequential_number": "",
                "errors": ["CIN cannot be empty"],
            }

        if len(cleaned) != 21:
            errors.append(
                f"CIN must be exactly 21 characters, got {len(cleaned)}"
            )
            return {
                "valid": False,
                "cin": cleaned,
                "listing_status": "",
                "nic_code": "",
                "state_code": "",
                "state_name": "",
                "year_of_incorporation": "",
                "company_type_code": "",
                "company_type": "",
                "sequential_number": "",
                "errors": errors,
            }

        if not CIN_RE.match(cleaned):
            errors.append("CIN format is invalid")
            return {
                "valid": False,
                "cin": cleaned,
                "listing_status": "",
                "nic_code": "",
                "state_code": "",
                "state_name": "",
                "year_of_incorporation": "",
                "company_type_code": "",
                "company_type": "",
                "sequential_number": "",
                "errors": errors,
            }

        # Decode fields
        listing_char = cleaned[0]
        listing_status = "Listed" if listing_char == "L" else "Unlisted"
        nic_code = cleaned[1:6]
        state_code = cleaned[6:8]
        year_of_incorporation = cleaned[8:12]
        company_type_code = cleaned[12:15]
        sequential_number = cleaned[15:21]

        state_name = CIN_STATE_CODES.get(state_code, "Unknown")
        if state_name == "Unknown":
            errors.append(f"Unrecognised state code in CIN: {state_code}")

        company_type = COMPANY_TYPES.get(company_type_code, "Unknown")
        if company_type == "Unknown":
            errors.append(
                f"Unrecognised company type code: {company_type_code}"
            )

        # Basic year check
        year_int = int(year_of_incorporation)
        if year_int < 1850 or year_int > 2100:
            errors.append(
                f"Year of incorporation {year_of_incorporation} is out of plausible range"
            )

        return {
            "valid": len(errors) == 0,
            "cin": cleaned,
            "listing_status": listing_status,
            "nic_code": nic_code,
            "state_code": state_code,
            "state_name": state_name,
            "year_of_incorporation": year_of_incorporation,
            "company_type_code": company_type_code,
            "company_type": company_type,
            "sequential_number": sequential_number,
            "errors": errors,
        }

    except Exception as exc:
        return {
            "valid": False,
            "cin": str(cin) if cin else "",
            "listing_status": "",
            "nic_code": "",
            "state_code": "",
            "state_name": "",
            "year_of_incorporation": "",
            "company_type_code": "",
            "company_type": "",
            "sequential_number": "",
            "errors": [f"CIN validation failed: {exc}"],
        }
