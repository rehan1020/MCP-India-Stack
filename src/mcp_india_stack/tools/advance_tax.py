"""Advance tax calculator for Indian income tax."""

from __future__ import annotations

from typing import Any


def calculate_advance_tax(
    estimated_income: float | None = None,
    regime: str = "new",
    taxpayer_type: str = "individual",
    existing_tds: float = 0,
    tax_liability: float | None = None,
) -> dict[str, Any]:
    """Calculate quarterly advance tax installment schedule.

    Under Section 234B and 234C, interest is levied if advance tax is not paid.
    This tool calculates the due dates and amounts.

    Args:
        estimated_income: Estimated total income for the financial year.
        regime: 'new' or 'old' tax regime.
        taxpayer_type: 'individual', 'senior_citizen', 'super_senior_citizen'.
        existing_tds: TDS already deducted or to be deducted.
        tax_liability: If provided, use this as the total tax liability directly
                       (instead of computing from estimated_income).

    Returns:
        Dict with quarterly breakdown and interest calculations.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Validate: need either tax_liability or estimated_income
    if tax_liability is None and estimated_income is None:
        errors.append("Provide either tax_liability or estimated_income")
    if tax_liability is not None and tax_liability < 0:
        errors.append("tax_liability cannot be negative")
    if estimated_income is not None and estimated_income <= 0 and tax_liability is None:
        errors.append("Estimated income must be positive")
    if existing_tds < 0:
        errors.append("Existing TDS cannot be negative")

    if errors:
        return {
            "total_tax_liability": 0.0,
            "advance_tax_due": 0.0,
            "installments": [],
            "errors": errors,
            "warnings": warnings,
        }

    # Determine total tax: use provided liability or compute from income
    if tax_liability is not None:
        total_tax = tax_liability  # Use as-is, do NOT recompute
    else:
        from mcp_india_stack.tools.income_tax import calculate_income_tax as calc_income_tax

        tax_result = calc_income_tax(
            gross_income=estimated_income or 0.0,
            regime=regime,
            taxpayer_type=taxpayer_type,
            deduction_80c=0,
            deduction_80d_self=0,
            deduction_80d_parents=0,
            deduction_80d_senior_parents=False,
            deduction_80ccd_nps=0,
            deduction_24b=0,
            other_deductions=0,
        )

        if tax_result.get("data"):
            total_tax = tax_result.get("data", {}).get("total_tax", 0)
        elif tax_result.get("new_regime"):
            total_tax = tax_result.get("new_regime", {}).get("total_tax", 0)
        elif tax_result.get("old_regime"):
            total_tax = tax_result.get("old_regime", {}).get("total_tax", 0)
        else:
            total_tax = 0

    net_tax_liability = max(0, total_tax - existing_tds)

    if net_tax_liability < 10000:
        warnings.append("Advance tax not required if net tax liability is below Rs 10,000")
        return {
            "total_tax_liability": round(total_tax, 2),
            "existing_tds": existing_tds,
            "net_tax_liability": round(net_tax_liability, 2),
            "advance_tax_due": 0.0,
            "installments": [],
            "is_advance_tax_required": False,
            "errors": errors,
            "warnings": warnings,
        }

    advance_tax_due = net_tax_liability

    # Both cumulative and incremental amounts for clarity
    installment_schedule: list[dict[str, Any]] = [
        {"quarter": "Q1", "due_date": "June 15", "cumulative_pct": 15, "incremental_pct": 15},
        {"quarter": "Q2", "due_date": "September 15", "cumulative_pct": 45, "incremental_pct": 30},
        {"quarter": "Q3", "due_date": "December 15", "cumulative_pct": 75, "incremental_pct": 30},
        {"quarter": "Q4", "due_date": "March 15", "cumulative_pct": 100, "incremental_pct": 25},
    ]

    for inst in installment_schedule:
        inst["cumulative_amount"] = round(advance_tax_due * inst["cumulative_pct"] / 100, 2)
        inst["installment_amount"] = round(advance_tax_due * inst["incremental_pct"] / 100, 2)
        # Backward compat: "amount" now = installment (incremental) amount
        inst["amount"] = inst["installment_amount"]
        # Keep "percentage" key for backward compat (cumulative)
        inst["percentage"] = inst["cumulative_pct"]

    return {
        "total_tax_liability": round(total_tax, 2),
        "existing_tds": existing_tds,
        "net_tax_liability": round(net_tax_liability, 2),
        "advance_tax_due": round(advance_tax_due, 2),
        "regime": regime,
        "taxpayer_type": taxpayer_type,
        "is_advance_tax_required": True,
        "installments": installment_schedule,
        "interest_rules": {
            "section_234b": "1% per month Simple interest if tax paid after due date"
            " but before assessment",
            "section_234c": "1% per month Simple interest on each installment delayed",
            "note": "Interest under 234C not levied if shortfall paid in next installment",
        },
        "errors": errors,
        "warnings": warnings,
    }


def calculate_interest_penalty(
    installment_amount: float,
    days_late: int,
    rate_per_month: float = 1.0,
) -> dict[str, Any]:
    """Calculate simple interest penalty for late advance tax payment.

    Args:
        installment_amount: Amount that was due.
        days_late: Number of days the payment was delayed.
        rate_per_month: Interest rate per month (default 1% per Section 234B/C).

    Returns:
        Dict with interest calculation breakdown.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if installment_amount < 0:
        errors.append("Installment amount cannot be negative")
    if days_late < 0:
        errors.append("Days late cannot be negative")

    if errors:
        return {
            "interest_penalty": 0.0,
            "errors": errors,
            "warnings": warnings,
        }

    months_late = days_late / 30.0
    months_late = max(0, min(months_late, 3))

    interest_penalty = installment_amount * (rate_per_month / 100) * months_late

    return {
        "installment_amount": installment_amount,
        "days_late": days_late,
        "months_late": round(months_late, 2),
        "rate_per_month": rate_per_month,
        "interest_penalty": round(interest_penalty, 2),
        "calculation": f"{installment_amount} x {rate_per_month}% x {months_late:.2f} months",
        "errors": errors,
        "warnings": warnings,
    }
