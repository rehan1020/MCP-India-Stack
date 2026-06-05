"""Income tax interest calculator (Sections 234A, 234B, 234C)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

DISCLAIMER = "Verify exact computation with your CA."


def calculate_income_tax_interest(
    total_tax_liability: float,
    advance_tax_paid: dict[str, float] | None = None,
    tds_deducted: float = 0.0,
    filing_date: str | None = None,
    due_date: str = "2025-07-31",
) -> dict[str, Any]:
    """Calculate interest under Sections 234A, 234B, 234C.

    Args:
        total_tax_liability: Total tax liability
        advance_tax_paid: Dict with "q1","q2","q3","q4" keys
        tds_deducted: TDS already deducted
        filing_date: YYYY-MM-DD when return filed (None if not filed)
        due_date: Due date for filing

    Returns:
        Dict with interest breakdown.
    """
    if advance_tax_paid is None:
        advance_tax_paid = {}

    net_tax = max(0, total_tax_liability - tds_deducted)
    total_advance = sum(advance_tax_paid.values())

    interest_234a = 0.0
    interest_234b = 0.0
    interest_234c = 0.0
    q_shortfalls = []

    if filing_date and filing_date != "pending":
        try:
            filing_dt = datetime.strptime(filing_date, "%Y-%m-%d")
            due_dt = datetime.strptime(due_date, "%Y-%m-%d")
            if filing_dt > due_dt:
                months = max(1, (filing_dt - due_dt).days // 30)
                interest_234a = net_tax * 0.01 * months
        except ValueError:
            pass

    if total_advance < 0.90 * net_tax:
        shortfall = net_tax - total_advance
        interest_234b = shortfall * 0.01 * 3

    required_pct = [0.15, 0.45, 0.75, 1.0]
    quarters = ["Q1_Jun15", "Q2_Sep15", "Q3_Dec15", "Q4_Mar15"]

    # Fix: use cumulative paid vs cumulative required for 234C
    cumulative_paid = 0.0
    for i, (q, pct) in enumerate(zip(quarters, required_pct, strict=False)):
        q_key = f"q{i + 1}"
        q_paid = advance_tax_paid.get(q_key, 0)
        cumulative_paid += q_paid
        required_cumulative = net_tax * pct

        # Q4 (i==3) has no 234C interest
        if i < 3 and cumulative_paid < required_cumulative:
            shortfall = required_cumulative - cumulative_paid
            if shortfall > 0:
                interest = round(shortfall * 0.01 * 3, 2)
                q_shortfalls.append(
                    {
                        "quarter": q,
                        "cumulative_required": round(required_cumulative, 2),
                        "cumulative_paid": round(cumulative_paid, 2),
                        "shortfall": round(shortfall, 2),
                        "interest": interest,
                    }
                )
                interest_234c += interest

    total_interest = round(interest_234a + interest_234b + interest_234c, 2)

    return {
        "net_assessed_tax": net_tax,
        "section_234a": {
            "applicable": interest_234a > 0,
            "months_delayed": int(interest_234a / (net_tax * 0.01)) if net_tax > 0 else 0,
            "interest_amount": round(interest_234a, 2),
            "interest": round(interest_234a, 2),
        },
        "section_234b": {
            "applicable": interest_234b > 0,
            "shortfall": round(net_tax - total_advance, 2),
            "interest_amount": round(interest_234b, 2),
            "interest": round(interest_234b, 2),
        },
        "section_234c": {
            "applicable": len(q_shortfalls) > 0,
            "quarterly_shortfalls": q_shortfalls,
            "total_234c_interest": round(interest_234c, 2),
        },
        "total_interest_payable": total_interest,
        "disclaimer": DISCLAIMER,
    }
