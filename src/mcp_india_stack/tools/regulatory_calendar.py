"""India tax & regulatory compliance calendar for FY2025-26."""

from __future__ import annotations

from typing import Any

REGULATORY_DEADLINES: list[dict[str, Any]] = [
    {
        "category": "Income Tax",
        "deadline": "2025-07-31",
        "description": "ITR filing deadline for individuals without audit",
        "applies_to": "Non-audit cases",
        "section": "Section 139(1)",
    },
    {
        "category": "Income Tax",
        "deadline": "2025-10-31",
        "description": "ITR filing deadline for audit cases",
        "applies_to": "Audit required",
        "section": "Section 139(1)",
    },
    {
        "category": "Income Tax",
        "deadline": "2025-11-30",
        "description": "Tax audit report filing (Form 3CA/3CB)",
        "applies_to": "Audit threshold met",
        "section": "Section 44AB",
    },
    {
        "category": "Income Tax",
        "deadline": "2026-03-31",
        "description": "Belated ITR filing for FY2024-25",
        "applies_to": "All taxpayers",
        "section": "Section 139(4)",
    },
    {
        "category": "TDS",
        "deadline": "2025-07-07",
        "description": "TDS/TCS deposit for June 2025 (quarterly)",
        "applies_to": "All deductors",
        "section": "Section 200(3)",
    },
    {
        "category": "TDS",
        "deadline": "2025-10-07",
        "description": "TDS/TCS deposit for Q2 FY2025-26",
        "applies_to": "All deductors",
        "section": "Section 200(3)",
    },
    {
        "category": "TDS",
        "deadline": "2026-01-07",
        "description": "TDS/TCS deposit for Q3 FY2025-26",
        "applies_to": "All deductors",
        "section": "Section 200(3)",
    },
    {
        "category": "TDS",
        "deadline": "2026-05-07",
        "description": "TDS/TCS deposit for Q4 FY2025-26",
        "applies_to": "All deductors",
        "section": "Section 200(3)",
    },
    {
        "category": "TDS",
        "deadline": "2025-05-31",
        "description": "TDS Certificate (Form 16) for Q4 FY2024-25",
        "applies_to": "Employers",
        "section": "Section 192",
    },
    {
        "category": "TDS",
        "deadline": "2025-06-15",
        "description": "TDS Certificate (Form 16A) for Q4 FY2024-25",
        "applies_to": "Non-salary deductors",
        "section": "Section 200(3)",
    },
    {
        "category": "TDS",
        "deadline": "2025-05-31",
        "description": "Annual TDS Statement (Form 24Q) for FY2024-25",
        "applies_to": "All employers",
        "section": "Section 206A",
    },
    {
        "category": "GST",
        "deadline": "2025-07-20",
        "description": "GSTR-3B return for June 2025",
        "applies_to": "Monthly filers",
        "section": "Section 39",
    },
    {
        "category": "GST",
        "deadline": "2025-07-22",
        "description": "GSTR-1 return for June 2025",
        "applies_to": "Monthly filers",
        "section": "Section 37",
    },
    {
        "category": "GST",
        "deadline": "2025-09-20",
        "description": "GSTR-3B return for Q1 FY2025-26 (quarterly)",
        "applies_to": "Quarterly filers",
        "section": "Section 39",
    },
    {
        "category": "GST",
        "deadline": "2025-12-31",
        "description": "GSTR-9 annual return for FY2024-25",
        "applies_to": "Regular taxpayers",
        "section": "Section 44",
    },
    {
        "category": "GST",
        "deadline": "2026-03-31",
        "description": "GSTR-9C reconciliation statement for FY2024-25",
        "applies_to": "Audit threshold",
        "section": "Section 44",
    },
    {
        "category": "PF/ESIC",
        "deadline": "2025-05-15",
        "description": "EPF contribution for April 2025",
        "applies_to": "All establishments",
        "section": "EPF Act Section 7",
    },
    {
        "category": "PF/ESIC",
        "deadline": "2025-06-15",
        "description": "ESIC contribution for April 2025",
        "applies_to": "Covered establishments",
        "section": "ESIC Act Section 7",
    },
    {
        "category": "PF/ESIC",
        "deadline": "2025-04-30",
        "description": "PF ECR filing for March 2025",
        "applies_to": "All establishments",
        "section": "EPF Scheme",
    },
    {
        "category": "ROC",
        "deadline": "2025-08-31",
        "description": "MCA Form AOC-4 for FY2024-25",
        "applies_to": "Companies",
        "section": "Companies Act 134",
    },
    {
        "category": "ROC",
        "deadline": "2025-09-30",
        "description": "MCA Form MGT-7 (Annual Return) for FY2024-25",
        "applies_to": "Companies",
        "section": "Companies Act 92",
    },
    {
        "category": "ROC",
        "deadline": "2025-10-31",
        "description": "Form ADT-3 ( Auditor appointment) for FY2025-26",
        "applies_to": "Companies",
        "section": "Companies Act 139",
    },
    {
        "category": "Professional Tax",
        "deadline": "2025-03-31",
        "description": "Professional tax (varies by state)",
        "applies_to": "Salaried/Self-employed",
        "section": "State PT Act",
    },
    {
        "category": "Advance Tax",
        "deadline": "2025-06-15",
        "description": "Advance tax installment Q1 FY2025-26",
        "applies_to": "Taxpayers > 10k liability",
        "section": "Section 211",
    },
    {
        "category": "Advance Tax",
        "deadline": "2025-09-15",
        "description": "Advance tax installment Q2 FY2025-26",
        "applies_to": "Taxpayers > 10k liability",
        "section": "Section 211",
    },
    {
        "category": "Advance Tax",
        "deadline": "2025-12-15",
        "description": "Advance tax installment Q3 FY2025-26",
        "applies_to": "Taxpayers > 10k liability",
        "section": "Section 211",
    },
    {
        "category": "Advance Tax",
        "deadline": "2026-03-15",
        "description": "Advance tax installment Q4 FY2025-26",
        "applies_to": "Taxpayers > 10k liability",
        "section": "Section 211",
    },
    {
        "category": "VDA",
        "deadline": "2025-05-31",
        "description": "Form 64D for TDS on Virtual Digital Assets (Q4)",
        "applies_to": "Crypto exchanges/deductors",
        "section": "Section 194S",
    },
]


def get_regulatory_deadlines(
    category: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """Get India's tax & regulatory deadlines for FY2025-26.

    Args:
        category: Filter by category (Income Tax, TDS, GST, PF/ESIC, ROC, etc.)
        from_date: Start date filter (YYYY-MM-DD)
        to_date: End date filter (YYYY-MM-DD)

    Returns:
        Deadlines matching the filters, grouped by month
    """
    from datetime import date

    filtered = REGULATORY_DEADLINES

    if category:
        filtered = [d for d in filtered if d["category"].lower() == category.lower()]

    if from_date:
        from_dt = date.fromisoformat(from_date)
        filtered = [d for d in filtered if date.fromisoformat(d["deadline"]) >= from_dt]

    if to_date:
        to_dt = date.fromisoformat(to_date)
        filtered = [d for d in filtered if date.fromisoformat(d["deadline"]) <= to_dt]

    grouped: dict[str, list[dict[str, Any]]] = {}
    for deadline in filtered:
        month = deadline["deadline"][:7]
        if month not in grouped:
            grouped[month] = []
        grouped[month].append(deadline)

    sorted_months = sorted(grouped.keys())

    return {
        "fy": "FY2025-26",
        "total_deadlines": len(filtered),
        "deadlines_by_month": {m: grouped[m] for m in sorted_months},
    }
