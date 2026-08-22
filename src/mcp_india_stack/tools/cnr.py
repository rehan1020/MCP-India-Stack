from __future__ import annotations

import re
from typing import Any, Callable, Optional

from mcp_india_stack.utils.responses import build_response


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    """Hoist data keys to top-level for backwards compatibility."""
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


decode_state_code_func: Optional[Callable[[str], dict[str, Any]]] = None
try:
    from mcp_india_stack.tools.state_code import decode_state_code
    decode_state_code_func = decode_state_code
except ImportError:
    pass


def decode_cnr_number(cnr: str) -> dict[str, Any]:
    """
    Decode an Indian Court Case Number Record (CNR).

    Input:
    - cnr (str): The 16-character CNR number.

    Output: cnr, state_code, court_establishment_code, sequence_number,
    filing_year, is_structurally_valid, success

    Example prompt: "Decode CNR number DLCT010012342024"

    Limitations: Structural validation only, does not verify existence in court databases.
    """
    errors: list[str] = []
    warnings: list[str] = []

    cnr_clean = str(cnr).strip().upper()
    is_structurally_valid = True

    if len(cnr_clean) != 16:
        is_structurally_valid = False
        errors.append(f"CNR must be exactly 16 characters. Got {len(cnr_clean)} characters.")

    if not re.match(r"^[A-Z]{2}[A-Z0-9]{2}[0-9]{8}[0-9]{4}$", cnr_clean) and len(cnr_clean) == 16:
        is_structurally_valid = False
        warnings.append("CNR format usually follows SSCC NNNNNNNN YYYY pattern.")

    state_code = cnr_clean[0:2] if len(cnr_clean) >= 2 else ""
    court_establishment_code = cnr_clean[0:4] if len(cnr_clean) >= 4 else ""
    sequence_number = cnr_clean[4:12] if len(cnr_clean) >= 12 else ""
    filing_year = cnr_clean[12:16] if len(cnr_clean) == 16 else ""

    if decode_state_code_func and state_code:
        try:
            state_info = decode_state_code_func(state_code)
            if state_info and state_info.get("success"):
                pass  # Successfully validated
            else:
                warnings.append(f"State code {state_code} could not be resolved.")
        except Exception:
            warnings.append(f"Failed to lookup state code {state_code}.")

    data = {
        "cnr": cnr_clean,
        "state_code": state_code,
        "court_establishment_code": court_establishment_code,
        "sequence_number": sequence_number,
        "filing_year": filing_year,
        "is_structurally_valid": is_structurally_valid,
    }

    return _flatten(
        build_response(success=len(errors) == 0, data=data, errors=errors, warnings=warnings)
    )
