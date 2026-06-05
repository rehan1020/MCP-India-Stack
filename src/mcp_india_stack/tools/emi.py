"""EMI (Equated Monthly Installment) calculator."""

from __future__ import annotations

from typing import Any

DISCLAIMER = "Computed using standard reducing balance formula. Actual EMI may vary by lender."


def calculate_emi(  # noqa: C901
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
    loan_type: str = "other",
) -> dict[str, Any]:  # noqa: C901
    """Calculate EMI for a loan with year-by-year amortization schedule.

    Args:
        principal: Loan amount in INR.
        annual_interest_rate: Annual rate as percentage (e.g., 8.5 means 8.5%).
        tenure_months: Loan tenure in months.
        loan_type: "home", "personal", "car", "education", "other" - label only.

    Returns:
        Dict with EMI, total payment, total interest, and amortization schedule.
    """
    try:
        errors: list[str] = []

        if principal <= 0:
            errors.append("principal must be greater than 0")
        if annual_interest_rate < 0:
            errors.append("annual interest rate cannot be negative")
        if tenure_months < 1:
            errors.append("tenure_months must be at least 1")
        if tenure_months > 360:
            errors.append("tenure_months cannot exceed 360 months (30 years)")

        if loan_type not in ("home", "personal", "car", "education", "other"):
            errors.append("loan_type must be one of: home, personal, car, education, other")

        if errors:
            return {
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        if annual_interest_rate == 0:
            emi = round(principal / tenure_months, 2)
            total_payment = emi * tenure_months
            total_interest = 0.0
            amortization_yearly: list[dict[str, Any]] = []
        else:
            monthly_rate = annual_interest_rate / (12 * 100)
            factor = (1 + monthly_rate) ** tenure_months
            emi = round(principal * monthly_rate * factor / (factor - 1), 2)

            total_payment = emi * tenure_months
            total_interest = total_payment - principal

            amortization_yearly = []
            balance = principal

            for year in range(1, (tenure_months // 12) + 1):
                year_principal = 0.0
                year_interest = 0.0

                for _month in range(12):
                    if balance <= 0:
                        break
                    interest_payment = balance * monthly_rate
                    principal_payment = emi - interest_payment

                    year_interest += interest_payment
                    year_principal += min(principal_payment, balance)
                    balance -= principal_payment

                if year_principal > 0 or year_interest > 0:
                    amortization_yearly.append(
                        {
                            "year": year,
                            "principal_paid": round(year_principal, 2),
                            "interest_paid": round(year_interest, 2),
                            "outstanding_balance": round(max(0, balance), 2),
                        }
                    )

        interest_to_principal_ratio = round(total_interest / principal, 2) if principal > 0 else 0

        result: dict[str, Any] = {
            "principal": principal,
            "annual_interest_rate": annual_interest_rate,
            "tenure_months": tenure_months,
            "loan_type": loan_type,
            "emi": emi,
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "interest_to_principal_ratio": interest_to_principal_ratio,
            "amortization_yearly": amortization_yearly,
            "disclaimer": DISCLAIMER,
        }

        return result

    except Exception as exc:
        return {
            "principal": principal if isinstance(principal, (int, float)) else 0,
            "annual_interest_rate": annual_interest_rate
            if isinstance(annual_interest_rate, (int, float))
            else 0,
            "tenure_months": tenure_months if isinstance(tenure_months, int) else 0,
            "loan_type": loan_type if isinstance(loan_type, str) else "other",
            "errors": [f"EMI calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
