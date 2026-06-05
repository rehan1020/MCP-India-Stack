"""EPF and ESIC contribution calculator."""

from __future__ import annotations

from typing import Any

EPF_WAGE_CEILING = 15000
ESIC_WAGE_CEILING = 21000
EPS_CEILING = 1250

DISCLAIMER = (
    "Computed using standard EPF/ESIC rules. Actual amounts may vary by "
    "establishment type and wages structure. Verify with your HR/Finance."
)


def calculate_epf_esic(
    basic_wages: float,
    gross_wages: float,
    include_employer_share: bool = True,
    voluntary_pf_on_actual: bool = False,
) -> dict[str, Any]:
    """Calculate EPF and ESIC contributions for employer and employee.

    Args:
        basic_wages: Basic salary + DA per month in INR.
        gross_wages: Total gross monthly salary in INR.
        include_employer_share: If True, return employer costs.
        voluntary_pf_on_actual: If True, compute employee EPF on actual basic
            (VPF) instead of capping at ₹15,000 wage ceiling.

    Returns:
        Dict with EPF, ESIC breakdown and totals.
    """
    try:
        errors: list[str] = []

        if basic_wages <= 0:
            errors.append("basic_wages must be greater than 0")
        if gross_wages <= 0:
            errors.append("gross_wages must be greater than 0")
        if gross_wages < basic_wages:
            errors.append("gross_wages cannot be less than basic_wages")

        if errors:
            return {
                "basic_wages": basic_wages,
                "gross_wages": gross_wages,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        epf_base = min(basic_wages, EPF_WAGE_CEILING)

        # Statutory (capped) vs voluntary (actual) EPF
        employee_epf_statutory = round(epf_base * 0.12, 2)
        employee_epf_voluntary = round(basic_wages * 0.12, 2)

        # Employer EPS and EPF are always on capped base
        employer_eps = min(round(epf_base * 0.0833), EPS_CEILING)
        employer_epf_to_account = round(epf_base * 0.12, 2) - employer_eps

        edli = round(epf_base * 0.005, 2)
        epf_admin = round(epf_base * 0.005, 2)

        total_employer_epf_cost = employer_epf_to_account + employer_eps + edli + epf_admin

        # Determine employee EPF deduction based on voluntary flag
        epf_note = None
        if voluntary_pf_on_actual and basic_wages > EPF_WAGE_CEILING:
            employee_epf_deduction = employee_epf_voluntary
            epf_note = (
                f"Voluntary PF on actual basic ₹{basic_wages:,.0f}. "
                f"EPS still capped at ₹{EPS_CEILING:,}."
            )
        else:
            employee_epf_deduction = employee_epf_statutory
            if basic_wages > EPF_WAGE_CEILING:
                epf_note = (
                    f"Statutory EPF on wage ceiling ₹{EPF_WAGE_CEILING:,}. "
                    f"Pass voluntary_pf_on_actual=True for VPF on full salary."
                )

        esic_applicable = gross_wages <= ESIC_WAGE_CEILING

        if esic_applicable:
            employee_esic = round(gross_wages * 0.0075, 2)
            employer_esic = round(gross_wages * 0.0325, 2)
        else:
            employee_esic = 0.0
            employer_esic = 0.0

        employee_total_deductions = employee_epf_deduction + employee_esic

        employer_total_contributions = total_employer_epf_cost + employer_esic

        total_employer_monthly_cost = gross_wages + employer_total_contributions

        esic_note = None
        if not esic_applicable:
            esic_note = (
                f"Gross wages ₹{gross_wages:,.0f} exceeds ESIC ceiling of ₹{ESIC_WAGE_CEILING:,}"
            )

        result: dict[str, Any] = {
            "basic_wages": basic_wages,
            "gross_wages": gross_wages,
            "epf": {
                "employee_epf_deduction": employee_epf_deduction,
                "employee_epf_statutory": employee_epf_statutory,
                "employee_epf_voluntary": employee_epf_voluntary,
                "employer_epf_to_account": employer_epf_to_account,
                "employer_eps": employer_eps,
                "edli": edli,
                "epf_admin_charge": epf_admin,
                "total_employer_epf_cost": round(total_employer_epf_cost, 2),
                "voluntary_pf_on_actual": voluntary_pf_on_actual,
                "note": epf_note,
            },
            "esic": {
                "applicable": esic_applicable,
                "employee_esic": employee_esic,
                "employer_esic": employer_esic,
                "reason": esic_note if not esic_applicable else None,
            },
            "employee_total_deductions": round(employee_total_deductions, 2),
            "employer_total_contributions": round(employer_total_contributions, 2),
            "total_employer_monthly_cost": round(total_employer_monthly_cost, 2),
            "disclaimer": DISCLAIMER,
        }

        return result

    except Exception as exc:
        return {
            "basic_wages": basic_wages if isinstance(basic_wages, (int, float)) else 0,
            "gross_wages": gross_wages if isinstance(gross_wages, (int, float)) else 0,
            "errors": [f"EPF/ESIC calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
