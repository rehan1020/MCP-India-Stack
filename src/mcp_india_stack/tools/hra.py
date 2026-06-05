"""HRA Exemption calculator for Indian income tax."""

from __future__ import annotations

from typing import Any

# Section 10(13A): only these 4 are metros for HRA purposes
METRO_CITIES_HRA = frozenset(
    {
        "delhi",
        "new delhi",
        "mumbai",
        "bombay",
        "chennai",
        "madras",
        "kolkata",
        "calcutta",
    }
)

# These cities get 40% (non-metro for HRA), even though colloquially called "metros"
NON_METRO_NOTE_CITIES = frozenset({"bangalore", "bengaluru", "hyderabad", "pune", "ahmedabad"})


def _classify_city(city: str) -> tuple[str, str | None]:
    """Return (city_type, warning_if_any)."""
    c = city.lower().strip()
    if c in METRO_CITIES_HRA:
        return "metro", None
    warning = None
    if c in NON_METRO_NOTE_CITIES:
        warning = (
            f"{city.title()} is NOT a metro city for Section 10(13A) HRA purposes. "
            f"Only Delhi, Mumbai, Chennai, Kolkata qualify for 50% HRA. "
            f"Applying 40% (non-metro) rate."
        )
    return "non_metro", warning


def calculate_hra_exemption(
    basic_salary: float,
    hra_received: float,
    rent_paid: float,
    city_type: str = "non_metro",
    is_government_employee: bool = False,
) -> dict[str, Any]:
    """Calculate HRA exemption under Section 10(13A)."""
    errors: list[str] = []
    warnings: list[str] = []

    if basic_salary <= 0:
        errors.append("Basic salary must be positive")
    if hra_received < 0:
        errors.append("HRA received cannot be negative")
    if rent_paid < 0:
        errors.append("Rent paid cannot be negative")

    if errors:
        return {
            "exemption": 0.0,
            "taxable_hra": 0.0,
            "basic_salary": basic_salary,
            "hra_received": hra_received,
            "rent_paid": rent_paid,
            "city_type": city_type,
            "is_government_employee": is_government_employee,
            "errors": errors,
            "warnings": warnings,
        }

    annual_basic = basic_salary
    annual_rent = rent_paid

    if is_government_employee:
        exemption = min(hra_received, annual_rent - (annual_basic * 0.1))
    else:
        metro_limit = 0.5 if city_type == "metro" else 0.4
        rule1 = hra_received
        rule2 = annual_rent - (annual_basic * 0.1)
        rule3 = annual_basic * metro_limit
        exemption = min(rule1, rule2, rule3)

    exemption = max(0, exemption)
    taxable_hra = hra_received - exemption

    if rent_paid == 0:
        warnings.append(
            "No rent paid - HRA exemption is zero since rent > 10% of salary condition fails"
        )
    elif rent_paid <= annual_basic * 0.1:
        warnings.append("Rent paid is less than 10% of salary - check if HRA is correctly claimed")

    return {
        "exemption": round(exemption, 2),
        "exempt_hra": round(exemption, 2),
        "taxable_hra": round(taxable_hra, 2),
        "annual_basic_salary": round(annual_basic, 2),
        "annual_hra_received": round(hra_received, 2),
        "annual_rent_paid": round(annual_rent, 2),
        "city_type": city_type,
        "is_government_employee": is_government_employee,
        "breakdown": {
            "hra_received": hra_received,
            "rent_minus_10_percent_salary": max(0, annual_rent - (annual_basic * 0.1)),
            "50_percent_metro_40_percent_nonmetro": annual_basic
            * (0.5 if city_type == "metro" else 0.4),
        },
        "errors": errors,
        "warnings": warnings,
    }


def calculate_hra_for_salary_structure(
    monthly_basic: float,
    monthly_hra: float,
    monthly_rent: float,
    city: str,
    is_government: bool = False,
) -> dict[str, Any]:
    """Calculate HRA using monthly figures with auto city detection."""
    city_type, city_warning = _classify_city(city)

    result = calculate_hra_exemption(
        basic_salary=monthly_basic * 12,
        hra_received=monthly_hra * 12,
        rent_paid=monthly_rent * 12,
        city_type=city_type,
        is_government_employee=is_government,
    )

    if city_warning:
        result.setdefault("warnings", []).append(city_warning)

    result["monthly_exemption"] = round(result["exemption"] / 12, 2)
    result["monthly_taxable_hra"] = round(result["taxable_hra"] / 12, 2)

    return result
