"""Indian driving license number validation."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from mcp_india_stack.authenticity.rules import create_driving_license_authenticity
from mcp_india_stack.utils.responses import build_response

# Standard format: SS RR YYYY NNNNNNN (state=2, RTO=2, year=4, serial=7 = 15 chars)
DL_STANDARD_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[0-9]{4}[0-9]{7}$")

DISCLAIMER = "Format validation only. Cannot verify license validity or status."

# Two-letter state abbreviations used in DL numbers
DL_STATE_CODES: dict[str, str] = {
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
    "OR": "Odisha",  # Legacy code
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


def validate_driving_license(dl_number: str) -> dict[str, Any]:
    """Validate an Indian driving license number format.

    Standard post-Sarathi format: [A-Z]{2}[0-9]{2}[0-9]{4}[0-9]{7} (15 chars).
    Extracts state code, RTO code, year of issue, and serial number.

    Args:
        dl_number: Driving license number string.

    Returns:
        Dict with validation results and decoded segments.
    """
    try:
        if dl_number is None:
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "dl_number": "",
                    "state_code": "",
                    "state_name": "",
                    "rto_code": "",
                    "year_of_issue": "",
                    "serial": "",
                },
                errors=["Driving license number is required"],
                source="offline_static",
            )

        # Normalise: strip whitespace, hyphens, convert to upper
        cleaned = re.sub(r"[\s\-]", "", str(dl_number).strip().upper())
        errors: list[str] = []

        if not cleaned:
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "dl_number": "",
                    "state_code": "",
                    "state_name": "",
                    "rto_code": "",
                    "year_of_issue": "",
                    "serial": "",
                },
                errors=["Driving license number cannot be empty"],
                source="offline_static",
            )

        # Standard 15-character format
        if DL_STANDARD_RE.match(cleaned):
            state_code = cleaned[0:2]
            rto_code = cleaned[2:4]
            year_of_issue = cleaned[4:8]
            serial = cleaned[8:15]

            state_name = DL_STATE_CODES.get(state_code, "Unknown")
            state_valid = state_name != "Unknown"
            if not state_valid:
                errors.append(f"Unrecognised state code: {state_code}")

            rto_valid = rto_code.isdigit() and len(rto_code) == 2

            # Year sanity check
            try:
                year_int = int(year_of_issue)
                year_valid = 1900 <= year_int <= date.today().year
            except ValueError:
                year_valid = False

            if not year_valid:
                errors.append(
                    f"Year of issue {year_of_issue} is out of "
                    f"plausible range [1900, {date.today().year}]"
                )

            valid = len(errors) == 0
            auth = create_driving_license_authenticity(
                dl=cleaned,
                valid=valid,
                state_valid=state_valid,
                rto_valid=rto_valid,
                year_valid=year_valid,
            )

            return build_response(
                success=valid,
                data={
                    "valid": valid,
                    "dl_number": cleaned,
                    "state_code": state_code,
                    "state_name": state_name,
                    "rto_code": rto_code,
                    "year_of_issue": year_of_issue,
                    "serial": serial,
                },
                errors=errors,
                source="offline_static",
                validated_by=["format_check"],
                authenticity=auth,
            )

        # Non-standard but plausible length (13-16 chars, alphanumeric)
        auth_invalid = create_driving_license_authenticity(
            dl=cleaned,
            valid=False,
            state_valid=False,
            rto_valid=False,
            year_valid=False,
        )
        if 13 <= len(cleaned) <= 16 and cleaned.isalnum():
            return build_response(
                success=False,
                data={
                    "valid": False,
                    "dl_number": cleaned,
                    "state_code": cleaned[0:2] if len(cleaned) >= 2 else "",
                    "state_name": "",
                    "rto_code": "",
                    "year_of_issue": "",
                    "serial": "",
                },
                errors=[
                    "Does not match standard post-Sarathi DL format. "
                    "May be a pre-Sarathi or state-specific format."
                ],
                source="offline_static",
                authenticity=auth_invalid,
            )

        # Clearly invalid
        if len(cleaned) < 13 or len(cleaned) > 16:
            errors.append(f"Driving license number should be 13-16 characters, got {len(cleaned)}")
        else:
            errors.append("Driving license number contains invalid characters")

        return build_response(
            success=False,
            data={
                "valid": False,
                "dl_number": cleaned,
                "state_code": "",
                "state_name": "",
                "rto_code": "",
                "year_of_issue": "",
                "serial": "",
            },
            errors=errors,
            source="offline_static",
            authenticity=auth_invalid,
        )

    except Exception as exc:
        auth_exc = create_driving_license_authenticity(
            dl=str(dl_number) if dl_number else "",
            valid=False,
            state_valid=False,
            rto_valid=False,
            year_valid=False,
        )
        return build_response(
            success=False,
            data={
                "valid": False,
                "dl_number": str(dl_number) if dl_number else "",
                "state_code": "",
                "state_name": "",
                "rto_code": "",
                "year_of_issue": "",
                "serial": "",
            },
            errors=[f"Driving license validation failed: {exc}"],
            source="offline_static",
            authenticity=auth_exc,
        )
