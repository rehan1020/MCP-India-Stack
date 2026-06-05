"""AA (Account Aggregator) consent request builder - offline."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

PURPOSE_CODE_MAP: dict[str, str] = {
    "101": "Wealth management",
    "102": "Customer spending analysis",
    "103": "Tax filing",
    "104": "Financial planning",
    "105": "Credit risk assessment",
    "106": "Loan eligibility check",
}

FI_TYPE_VALID = [
    "DEPOSIT",
    "MUTUAL_FUNDS",
    "INSURANCE",
    "NPS",
    "EQUITIES",
    "GSTIN_DATA",
    "CREDIT_CARD",
    "RECURRING_DEPOSIT",
]

DISCLAIMER = (
    "This payload is constructed per ReBIT AA Tech Spec v2.0. "
    "Verify schema version with your AA operator before use."
)


def build_aa_consent_request(
    customer_id: str,
    fi_types: list[str],
    date_range_from: str,
    date_range_to: str,
    consent_expiry_days: int = 30,
    purpose_code: str = "101",
    fetch_type: str = "ONETIME",
    frequency_unit: str | None = None,
    frequency_value: int | None = None,
) -> dict[str, Any]:
    """Construct AA consent request JSON per ReBIT spec.

    Args:
        customer_id: AA customer address (e.g., user@onemoney)
        fi_types: Financial information types to request
        date_range_from: YYYY-MM-DD - data fetch range start
        date_range_to: YYYY-MM-DD - data fetch range end
        consent_expiry_days: How many days consent remains valid
        purpose_code: ReBIT purpose code (default "101")
        fetch_type: "ONETIME" or "PERIODIC"
        frequency_unit: "HOUR", "DAY", "MONTH", "YEAR" - for PERIODIC
        frequency_value: Numeric frequency - for PERIODIC

    Returns:
        Dict with consent request payload and validation.
    """
    errors: list[str] = []

    if not customer_id or "@" not in customer_id:
        errors.append("customer_id must be a valid AA address (user@provider)")

    for ft in fi_types:
        if ft not in FI_TYPE_VALID:
            errors.append(f"Invalid fi_type '{ft}'. Valid: {FI_TYPE_VALID}")

    try:
        from_dt = datetime.strptime(date_range_from, "%Y-%m-%d")
        to_dt = datetime.strptime(date_range_to, "%Y-%m-%d")
        if to_dt <= from_dt:
            errors.append("date_range_to must be after date_range_from")
    except ValueError:
        errors.append("Dates must be in YYYY-MM-DD format")

    if purpose_code not in PURPOSE_CODE_MAP:
        errors.append(
            f"Invalid purpose_code '{purpose_code}'. Valid: {list(PURPOSE_CODE_MAP.keys())}"
        )

    if fetch_type == "PERIODIC":
        if not frequency_unit or not frequency_value:
            errors.append("frequency_unit and frequency_value required for PERIODIC fetch")
        if frequency_unit not in ("HOUR", "DAY", "MONTH", "YEAR"):
            errors.append("frequency_unit must be HOUR, DAY, MONTH, or YEAR")

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "disclaimer": DISCLAIMER,
        }

    today = datetime.now()
    consent_start = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    consent_expiry = (today + timedelta(days=consent_expiry_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload: dict[str, Any] = {
        "consentStart": consent_start,
        "consentExpiry": consent_expiry,
        "consentMode": "VIEW",
        "fetchType": fetch_type,
        "consentTypes": ["TRANSACTIONS", "PROFILE", "SUMMARY"],
        "fiTypes": fi_types,
        "Purpose": {
            "code": purpose_code,
            "text": PURPOSE_CODE_MAP.get(purpose_code, "Unknown"),
        },
        "FIDataRange": {
            "from": date_range_from,
            "to": date_range_to,
        },
        "DataLife": {
            "unit": "MONTH",
            "value": 1,
        },
    }

    if fetch_type == "PERIODIC" and frequency_unit and frequency_value:
        payload["Frequency"] = {
            "unit": frequency_unit,
            "value": frequency_value,
        }

    return {
        "valid": True,
        "consent_request_payload": payload,
        "validation_notes": [],
        "next_step": (
            "Submit this payload to your AA's /Consent endpoint. "
            "Requires FIU registration with ReBIT."
        ),
        "disclaimer": DISCLAIMER,
    }
