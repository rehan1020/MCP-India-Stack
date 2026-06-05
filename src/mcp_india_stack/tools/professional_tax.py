"""Professional tax calculator by state."""

from __future__ import annotations

from typing import Any

# Monthly salary slabs with (threshold, monthly_pt) pairs.
# For each state, find the first threshold >= monthly salary.
PT_SLABS: dict[str, list[tuple[float, float]]] = {
    "MH": [(7500, 0), (10000, 175), (float("inf"), 200)],
    "KA": [(15000, 0), (29999, 150), (float("inf"), 200)],
    "WB": [(10000, 0), (15000, 110), (25000, 130), (40000, 150), (float("inf"), 200)],
    "TN": [
        (3500, 0),
        (5000, 15),
        (7500, 30),
        (10000, 60),
        (15000, 90),
        (25000, 135),
        (float("inf"), 225),
    ],
    "AP": [(20000, 0), (30000, 100), (40000, 150), (50000, 200), (float("inf"), 250)],
    "GJ": [(15000, 0), (30000, 80), (60000, 150), (float("inf"), 200)],
    "MP": [(22500, 0), (45000, 125), (float("inf"), 200)],
    "OR": [(15000, 0), (30000, 50), (float("inf"), 100)],
}

# Maharashtra February slab: > ₹10,000 monthly salary pays ₹300 in Feb instead of ₹200
MH_FEBRUARY_SLABS: list[tuple[float, float]] = [(7500, 0), (10000, 175), (float("inf"), 300)]

# State name aliases → state code mapping
STATE_NAME_MAP: dict[str, str] = {
    "MAHARASHTRA": "MH",
    "KARNATAKA": "KA",
    "WEST BENGAL": "WB",
    "TAMIL NADU": "TN",
    "ANDHRA PRADESH": "AP",
    "GUJARAT": "GJ",
    "MADHYA PRADESH": "MP",
    "ODISHA": "OR",
    "ORISSA": "OR",
}

# States with no professional tax
NO_PT_STATES = {
    "DL",
    "DELHI",
    "RJ",
    "RAJASTHAN",
    "UP",
    "UTTAR PRADESH",
    "HR",
    "HARYANA",
    "UK",
    "UTTARAKHAND",
    "HP",
    "HIMACHAL PRADESH",
    "JK",
    "JAMMU AND KASHMIR",
    "GA",
    "GOA",
}

DISCLAIMER = "Verify with current state government gazette."


def _get_monthly_pt(monthly_salary: float, slabs: list[tuple[float, float]]) -> float:
    """Get monthly PT amount for a given salary from slab table."""
    for threshold, rate in slabs:
        if monthly_salary <= threshold:
            return rate
    return 0.0


def _resolve_state_code(state_input: str) -> str:
    """Resolve state name or code to a 2-character state code."""
    upper = state_input.strip().upper()
    # Direct code match
    if upper in PT_SLABS:
        return upper
    # Name-based lookup
    return STATE_NAME_MAP.get(upper, upper)


def calculate_professional_tax(
    gross_salary_monthly: float,
    state_code: str,
) -> dict[str, Any]:
    """Calculate state-wise professional tax.

    Args:
        gross_salary_monthly: Monthly gross salary
        state_code: State code (e.g., "MH", "KA") or full name (e.g., "Maharashtra")

    Returns:
        Dict with PT calculation including monthly, February, and annual amounts.
    """
    resolved_code = _resolve_state_code(state_code)

    # Check if state has no PT
    if resolved_code.upper() in NO_PT_STATES or state_code.strip().upper() in NO_PT_STATES:
        return {
            "state": state_code,
            "applicable": False,
            "annual_pt": 0,
            "monthly_pt": 0,
            "reason": f"No professional tax in state {state_code}",
            "disclaimer": DISCLAIMER,
        }

    if resolved_code not in PT_SLABS:
        return {
            "state": state_code,
            "applicable": False,
            "annual_pt": 0,
            "monthly_pt": 0,
            "reason": f"Professional tax data not available for state: {state_code}",
            "disclaimer": DISCLAIMER,
        }

    # Get monthly PT from slabs (applied to MONTHLY salary)
    monthly_pt = _get_monthly_pt(gross_salary_monthly, PT_SLABS[resolved_code])

    # Maharashtra: February has a different (higher) rate for the top slab
    if resolved_code == "MH":
        february_pt = _get_monthly_pt(gross_salary_monthly, MH_FEBRUARY_SLABS)
    else:
        february_pt = monthly_pt

    # Annual = 11 regular months + 1 February month
    annual_pt = (monthly_pt * 11) + february_pt

    return {
        "state": resolved_code,
        "gross_salary_monthly": gross_salary_monthly,
        "professional_tax_monthly": round(monthly_pt, 2),
        "february_pt": round(february_pt, 2),
        "professional_tax_annual": round(annual_pt, 2),
        "monthly_pt": round(monthly_pt, 2),
        "annual_pt": round(annual_pt, 2),
        "applicable": annual_pt > 0,
        "deductible_under_section_16": True,
        "note": (
            (
                f"Maharashtra charges ₹{int(february_pt)} in February."
                if resolved_code == "MH" and february_pt != monthly_pt
                else ""
            )
            + f" Annual total = ₹{annual_pt:,.0f}."
        ).strip(),
        "disclaimer": DISCLAIMER,
    }
