from __future__ import annotations

import functools
import json
import pathlib
from typing import Any


@functools.lru_cache(maxsize=1)
def _load_stamp_duty() -> dict[str, Any]:
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "legal" / "stamp_duty.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def calculate_stamp_duty(
    state_code: str, instrument_type: str, transaction_value: float
) -> dict[str, Any]:
    """
    Calculate stamp duty and registration fee for an instrument.

    Input:
    - state_code (str): 2-letter state code.
    - instrument_type (str): Type of instrument (e.g., "sale_deed").
    - transaction_value (float): Transaction value in rupees.

    Output: state_code, state_name, instrument_type, transaction_value,
    duty_amount, registration_fee, surcharge, total_payable, as_of, notes,
    errors, warnings

    Example prompt: "Calculate stamp duty for sale_deed of 10000000 in MH"

    Limitations: Stamp duty is subject to local surcharges and frequent changes.
    """
    errors: list[str] = []
    warnings: list[str] = [
        "Stamp duty frequently changes and depends on specific local variables "
        "(e.g., gender, municipal limits)"
    ]

    code = state_code.upper()
    data = _load_stamp_duty()

    state_data = data.get(code)
    if not state_data:
        errors.append(f"Stamp duty data not available for state {code}.")
        return {"errors": errors, "warnings": warnings}

    state_name = state_data.get("state_name", code)
    as_of = state_data.get("as_of", "unknown")
    notes = state_data.get("notes", "")

    instrument = state_data.get(instrument_type)
    if not instrument:
        errors.append(f"Instrument type '{instrument_type}' not found for state {code}.")
        return {"errors": errors, "warnings": warnings}

    duty_pct = float(instrument.get("duty_pct", 0))
    registration_pct = float(instrument.get("registration_pct", 0))
    surcharge_pct = float(instrument.get("surcharge_pct", 0))

    duty_amount = (transaction_value * duty_pct) / 100.0
    registration_fee = (transaction_value * registration_pct) / 100.0

    # Some states cap registration fee
    reg_cap = instrument.get("registration_cap")
    if reg_cap is not None and registration_fee > float(reg_cap):
        registration_fee = float(reg_cap)

    surcharge = (duty_amount * surcharge_pct) / 100.0
    total_payable = duty_amount + registration_fee + surcharge

    return {
        "state_code": code,
        "state_name": state_name,
        "instrument_type": instrument_type,
        "transaction_value": transaction_value,
        "duty_amount": round(duty_amount, 2),
        "registration_fee": round(registration_fee, 2),
        "surcharge": round(surcharge, 2),
        "total_payable": round(total_payable, 2),
        "as_of": as_of,
        "notes": notes,
        "errors": errors,
        "warnings": warnings,
    }
