from __future__ import annotations

import functools
import json
import pathlib
from typing import Any


@functools.lru_cache(maxsize=1)
def _load_court_fees() -> dict[str, Any]:
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "legal" / "court_fees.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def calculate_court_fee(  # noqa: C901
    state_code: str, suit_value: float, suit_type: str = "money"
) -> dict[str, Any]:
    """
    Calculate court fee for a given state, suit value, and suit type.

    Input:
    - state_code (str): 2-letter state code.
    - suit_value (float): Value of the suit in rupees.
    - suit_type (str): Type of suit ("money", "declaration", "injunction", "partition", "probate").

    Output: state_code, state_name, suit_type, suit_value,
    fee_amount, calculation_basis, as_of, errors, warnings

    Example prompt: "Calculate court fee for money suit of 500000 in MH"

    Limitations: Court fees are state-subject and may have been updated since last verification.
    """
    errors: list[str] = []
    warnings: list[str] = [
        "Court fees are state-subject and may have been updated since last verification"
    ]

    code = state_code.upper()
    data = _load_court_fees()

    state_data = data.get(code)
    if not state_data:
        errors.append(f"Court fee data not available for state {code}.")
        return {"errors": errors, "warnings": warnings}

    state_name = state_data.get("state_name", code)
    as_of = state_data.get("as_of", "unknown")

    fee_amount = 0.0
    calculation_basis = ""

    # Map 'money' to 'money_suit' for lookup
    lookup_type = "money_suit" if suit_type == "money" else suit_type

    rule = state_data.get(lookup_type)
    if not rule:
        errors.append(f"Suit type '{suit_type}' not found for state {code}.")
        return {"errors": errors, "warnings": warnings}

    if isinstance(rule, list):
        # Handle slabs for money_suit
        calculation_basis = "slab_based"
        for slab in rule:
            up_to = slab.get("up_to")
            above = slab.get("above")
            if up_to is not None and suit_value <= float(up_to):
                if "fee" in slab:
                    fee_amount = float(slab["fee"])
                    calculation_basis += f"_fixed_{fee_amount}"
                elif "fee_pct" in slab:
                    fee_amount = (suit_value * float(slab["fee_pct"])) / 100.0
                    if "min_fee" in slab and fee_amount < float(slab["min_fee"]):
                        fee_amount = float(slab["min_fee"])
                break
            elif above is not None and suit_value > float(above):
                if "fee_pct" in slab:
                    fee_amount = (suit_value * float(slab["fee_pct"])) / 100.0
                    if "base_fee" in slab:
                        fee_amount += float(slab["base_fee"])
                    if "max_fee" in slab and fee_amount > float(slab["max_fee"]):
                        fee_amount = float(slab["max_fee"])
                break
    elif isinstance(rule, dict):
        if "fixed" in rule:
            fee_amount = float(rule["fixed"])
            calculation_basis = "fixed_fee"
        elif "fee_pct" in rule:
            fee_amount = (suit_value * float(rule["fee_pct"])) / 100.0
            calculation_basis = f"percentage_{rule['fee_pct']}%"
            if "max_fee" in rule and fee_amount > float(rule["max_fee"]):
                fee_amount = float(rule["max_fee"])
                calculation_basis += "_capped"
    else:
        errors.append("Invalid rule format in data file.")

    return {
        "state_code": code,
        "state_name": state_name,
        "suit_type": suit_type,
        "suit_value": suit_value,
        "fee_amount": round(fee_amount, 2),
        "calculation_basis": calculation_basis,
        "as_of": as_of,
        "errors": errors,
        "warnings": warnings,
    }
