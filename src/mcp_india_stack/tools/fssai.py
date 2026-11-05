"""FSSAI License Validator for India Stack."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from mcp_india_stack.authenticity.rules import create_fssai_authenticity

FSSAI_RE = re.compile(r"^\d{14}$")


def validate_fssai(license_number: str) -> dict[str, Any]:
    """Validate FSSAI license number (14-digit format).

    The 14-digit FSSAI license encodes:
    - Digits 1-2: State code
    - Digits 3-4: Year of registration
    - Digit 5: License type (1=Central, 2=State, 3=State based on turnover)
    - Digits 6-14: Sequence number

    Args:
        license_number: 14-digit FSSAI license number

    Returns:
        Dict with validation result and decoded information
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not license_number:
        errors.append("FSSAI license number is required")
        auth = create_fssai_authenticity(
            fssai="",
            valid=False,
            state_valid=False,
            year_valid=False,
            license_type_valid=False,
        )
        return {
            "valid": False,
            "license_number": "",
            "errors": errors,
            "warnings": warnings,
            "authenticity": auth,
        }

    # Normalize: remove any spaces/dashes, keep only digits
    normalized = re.sub(r"[^0-9]", "", license_number.strip().upper())

    if len(normalized) != 14:
        errors.append(f"FSSAI license must be 14 digits, got {len(normalized)}")
        auth = create_fssai_authenticity(
            fssai=normalized,
            valid=False,
            state_valid=False,
            year_valid=False,
            license_type_valid=False,
        )
        return {
            "valid": False,
            "license_number": license_number,
            "normalized_input": normalized,
            "errors": errors,
            "warnings": warnings,
            "authenticity": auth,
        }

    if not FSSAI_RE.match(normalized):
        errors.append("FSSAI license must be exactly 14 digits")
        auth = create_fssai_authenticity(
            fssai=normalized,
            valid=False,
            state_valid=False,
            year_valid=False,
            license_type_valid=False,
        )
        return {
            "valid": False,
            "license_number": license_number,
            "normalized_input": normalized,
            "errors": errors,
            "warnings": warnings,
            "authenticity": auth,
        }

    # Decode the license
    state_code = int(normalized[0:2])
    year_str = normalized[2:4]
    license_type_code = normalized[4]
    sequence = normalized[5:]

    # Map license type
    license_types = {
        "1": "Central License",
        "2": "State License",
        "3": "State License (Turn-based)",
        "4": "License Certificate",
        "5": "Registration Certificate",
    }
    license_type = license_types.get(license_type_code, f"License Type {license_type_code}")

    # State codes (common ones)
    state_codes = {
        1: "Jammu & Kashmir",
        2: "Himachal Pradesh",
        3: "Punjab",
        4: "Chandigarh",
        5: "Uttarakhand",
        6: "Haryana",
        7: "Delhi",
        8: "Rajasthan",
        9: "Uttar Pradesh",
        10: "Bihar",
        11: "Sikkim",
        12: "Arunachal Pradesh",
        13: "Nagaland",
        14: "Manipur",
        15: "Mizoram",
        16: "Tripura",
        17: "Meghalaya",
        18: "Assam",
        19: "West Bengal",
        20: "Odisha",
        21: "Jharkhand",
        22: "Chhattisgarh",
        23: "Madhya Pradesh",
        24: "Gujarat",
        25: "Maharashtra",
        26: "Andhra Pradesh (Old)",
        27: "Karnataka",
        28: "Goa",
        29: "Lakshadweep",
        30: "Kerala",
        31: "Tamil Nadu",
        32: "Puducherry",
        33: "Andaman & Nicobar",
        34: "Telangana",
        35: "Andhra Pradesh (New)",
        99: "Central",
    }
    state = state_codes.get(state_code, f"Unknown ({state_code})")

    # Validate state code range
    if state_code > 35 and state_code != 99:
        warnings.append(f"Unusual state code: {state_code}. Please verify.")

    # Calculate year assuming 2000-based
    try:
        year = int(year_str) + 2000
        current_year = date.today().year
        year_valid = 2006 <= year <= current_year + 1  # FSSAI established in 2006
        if year > 2030 or not year_valid:
            warnings.append(f"Unusual license year: {year}")
    except ValueError:
        warnings.append("Could not decode license year")
        year = None
        year_valid = False

    state_valid = state_code in state_codes
    license_type_valid = license_type_code in ("1", "2", "3", "4", "5")
    valid = len(errors) == 0

    auth = create_fssai_authenticity(
        fssai=normalized,
        valid=valid,
        state_valid=state_valid,
        year_valid=year_valid,
        license_type_valid=license_type_valid,
    )

    return {
        "valid": valid,
        "license_number": license_number,
        "normalized_input": normalized,
        "state_code": state_code,
        "state_name": state,
        "license_year": year,
        "license_type_code": license_type_code,
        "license_type": license_type,
        "sequence_number": sequence,
        "errors": errors,
        "warnings": warnings,
        "authenticity": auth,
    }
