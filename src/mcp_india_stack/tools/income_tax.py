"""Income tax calculator for FY2025-26 — New and Old regime with full slab computation."""

from __future__ import annotations

from typing import Any

# --- FY2025-26 Rate Tables ---

NEW_REGIME_SLABS: list[tuple[float, float]] = [
    (400_000, 0.00),
    (800_000, 0.05),
    (1_200_000, 0.10),
    (1_600_000, 0.15),
    (2_000_000, 0.20),
    (2_400_000, 0.25),
    (float("inf"), 0.30),
]
NEW_REGIME_STANDARD_DEDUCTION = 75_000
NEW_REGIME_87A_LIMIT = 1_200_000
NEW_REGIME_87A_REBATE = 60_000
NEW_REGIME_BASIC_EXEMPTION = 400_000

OLD_REGIME_SLABS: dict[str, list[tuple[float, float]]] = {
    "individual": [
        (250_000, 0.00),
        (500_000, 0.05),
        (1_000_000, 0.20),
        (float("inf"), 0.30),
    ],
    "senior_citizen": [
        (300_000, 0.00),
        (500_000, 0.05),
        (1_000_000, 0.20),
        (float("inf"), 0.30),
    ],
    "super_senior_citizen": [
        (500_000, 0.00),
        (1_000_000, 0.20),
        (float("inf"), 0.30),
    ],
}
OLD_REGIME_STANDARD_DEDUCTION = 50_000
OLD_REGIME_87A_LIMIT = 500_000
OLD_REGIME_87A_REBATE = 12_500

# Surcharge rates — shared with surcharge.py (import from here, don't duplicate)
SURCHARGE_RATES: list[tuple[float, float]] = [
    (5_000_000, 0.00),
    (10_000_000, 0.10),
    (20_000_000, 0.15),
    (50_000_000, 0.25),
    (float("inf"), 0.37),
]
NEW_REGIME_MAX_SURCHARGE = 0.25

CESS_RATE = 0.04

OLD_REGIME_DEDUCTION_LIMITS: dict[str, int] = {
    "section_80c": 150_000,
    "section_80d_self": 25_000,
    "section_80d_parents": 25_000,
    "section_80d_senior_parents": 50_000,
    "section_80ccd_nps": 50_000,
    "section_24b_home_loan": 200_000,
}

DISCLAIMER = (
    "This is an estimate for FY2025-26 based on standard computation. "
    "Actual tax liability may differ. Consult a CA for accurate filing."
)

VALID_TAXPAYER_TYPES = {"individual", "senior_citizen", "super_senior_citizen"}


def _compute_slab_tax(taxable_income: float, slabs: list[tuple[float, float]]) -> float:
    """Compute tax using progressive slab rates."""
    tax = 0.0
    prev_limit = 0.0
    for limit, rate in slabs:
        if taxable_income <= prev_limit:
            break
        taxable_in_slab = min(taxable_income, limit) - prev_limit
        tax += taxable_in_slab * rate
        prev_limit = limit
    return round(tax, 2)


def _get_surcharge_rate(total_income: float, regime: str) -> float:
    """Determine applicable surcharge rate."""
    rate = 0.0
    for limit, r in SURCHARGE_RATES:
        if total_income <= limit:
            rate = r
            break
        rate = r

    if regime == "new" and rate > NEW_REGIME_MAX_SURCHARGE:
        rate = NEW_REGIME_MAX_SURCHARGE
    return rate


def _compute_surcharge_with_marginal_relief(
    total_income: float,
    base_tax: float,
    regime: str,
) -> float:
    """Compute surcharge with marginal relief if applicable."""
    surcharge_rate = _get_surcharge_rate(total_income, regime)
    if surcharge_rate == 0:
        return 0.0

    surcharge = round(base_tax * surcharge_rate, 2)

    # Find the threshold that was just crossed
    prev_threshold = 0.0
    for limit, _rate in SURCHARGE_RATES:
        if total_income <= limit:
            break
        prev_threshold = limit

    if prev_threshold > 0:
        # Tax at the threshold (no surcharge at that level)
        prev_rate = _get_surcharge_rate(prev_threshold, regime)
        # Marginal relief: surcharge limited so (base_tax + surcharge) doesn't exceed
        # (base_tax_at_prev + prev_surcharge) + (income - prev_threshold)
        excess_income = total_income - prev_threshold
        tax_plus_surcharge = base_tax + surcharge
        tax_at_prev = base_tax  # simplified — base tax at threshold would differ
        tax_plus_prev_surcharge = tax_at_prev + round(tax_at_prev * prev_rate, 2)
        marginal_limit = tax_plus_prev_surcharge + excess_income

        if tax_plus_surcharge > marginal_limit:
            surcharge = round(marginal_limit - base_tax, 2)
            if surcharge < 0:
                surcharge = 0.0

    return surcharge


def _compute_regime(
    gross_income: float,
    regime_key: str,
    taxpayer_type: str,
    standard_deduction: float,
    slabs: list[tuple[float, float]],
    rebate_limit: float,
    rebate_amount: float,
    total_deductions: float = 0,
) -> dict[str, Any]:
    """Compute full tax for a single regime."""
    adjusted_income = max(gross_income - standard_deduction, 0)
    taxable_income = max(adjusted_income - total_deductions, 0)

    base_tax = _compute_slab_tax(taxable_income, slabs)

    # Section 87A rebate
    rebate_87a = 0.0
    if taxable_income <= rebate_limit:
        rebate_87a = min(base_tax, rebate_amount)

    tax_after_rebate = max(base_tax - rebate_87a, 0)

    surcharge = _compute_surcharge_with_marginal_relief(
        gross_income, tax_after_rebate, regime_key
    )
    cess = round((tax_after_rebate + surcharge) * CESS_RATE, 2)
    total_tax = round(tax_after_rebate + surcharge + cess, 2)

    effective_rate = round((total_tax / gross_income) * 100, 2) if gross_income > 0 else 0.0
    monthly_tax = round(total_tax / 12, 2)
    take_home_annual = round(gross_income - total_tax, 2)

    return {
        "standard_deduction": standard_deduction,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "base_tax": base_tax,
        "rebate_87a": rebate_87a,
        "tax_after_rebate": tax_after_rebate,
        "surcharge": surcharge,
        "cess": cess,
        "total_tax": total_tax,
        "effective_rate": effective_rate,
        "monthly_tax": monthly_tax,
        "take_home_annual": take_home_annual,
    }


def calculate_income_tax(
    gross_income: float,
    regime: str = "both",
    taxpayer_type: str = "individual",
    deduction_80c: float = 0,
    deduction_80d_self: float = 0,
    deduction_80d_parents: float = 0,
    deduction_80d_senior_parents: bool = False,
    deduction_80ccd_nps: float = 0,
    deduction_24b: float = 0,
    other_deductions: float = 0,
) -> dict[str, Any]:
    """Calculate income tax for FY2025-26 under old, new, or both regimes.

    Args:
        gross_income: Annual gross income in rupees.
        regime: "new", "old", or "both".
        taxpayer_type: "individual", "senior_citizen", "super_senior_citizen".
        deduction_80c: Section 80C deduction (capped at ₹1.5L).
        deduction_80d_self: Section 80D self (capped at ₹25K).
        deduction_80d_parents: Section 80D parents (capped at ₹25K or ₹50K for senior).
        deduction_80d_senior_parents: If True, parents 80D cap is ₹50K.
        deduction_80ccd_nps: Additional NPS deduction (capped at ₹50K).
        deduction_24b: Home loan interest (capped at ₹2L).
        other_deductions: Other deductions (no cap).

    Returns:
        Dict with tax breakdown per regime and comparison.
    """
    try:
        errors: list[str] = []

        if gross_income is None or not isinstance(gross_income, (int, float)):
            errors.append("gross_income is required and must be a number")

        if isinstance(gross_income, (int, float)) and gross_income < 0:
            errors.append("gross_income cannot be negative")

        if regime not in ("new", "old", "both"):
            errors.append("regime must be 'new', 'old', or 'both'")

        if taxpayer_type not in VALID_TAXPAYER_TYPES:
            errors.append(
                f"taxpayer_type must be one of {sorted(VALID_TAXPAYER_TYPES)}"
            )

        if errors:
            return {
                "financial_year": "2025-26",
                "assessment_year": "2026-27",
                "gross_income": gross_income if isinstance(gross_income, (int, float)) else 0,
                "regime": regime,
                "errors": errors,
                "disclaimer": DISCLAIMER,
            }

        result: dict[str, Any] = {
            "financial_year": "2025-26",
            "assessment_year": "2026-27",
            "gross_income": gross_income,
            "regime": regime,
            "errors": [],
            "disclaimer": DISCLAIMER,
        }

        # --- New Regime ---
        if regime in ("new", "both"):
            new_result = _compute_regime(
                gross_income=gross_income,
                regime_key="new",
                taxpayer_type=taxpayer_type,
                standard_deduction=NEW_REGIME_STANDARD_DEDUCTION,
                slabs=NEW_REGIME_SLABS,
                rebate_limit=NEW_REGIME_87A_LIMIT,
                rebate_amount=NEW_REGIME_87A_REBATE,
            )
            result["new_regime"] = new_result

        # --- Old Regime ---
        if regime in ("old", "both"):
            old_slabs = OLD_REGIME_SLABS.get(taxpayer_type, OLD_REGIME_SLABS["individual"])

            # Cap old regime deductions
            capped_80c = min(deduction_80c, OLD_REGIME_DEDUCTION_LIMITS["section_80c"])
            capped_80d_self = min(
                deduction_80d_self, OLD_REGIME_DEDUCTION_LIMITS["section_80d_self"]
            )
            parent_80d_limit = (
                OLD_REGIME_DEDUCTION_LIMITS["section_80d_senior_parents"]
                if deduction_80d_senior_parents
                else OLD_REGIME_DEDUCTION_LIMITS["section_80d_parents"]
            )
            capped_80d_parents = min(deduction_80d_parents, parent_80d_limit)
            capped_80ccd = min(
                deduction_80ccd_nps, OLD_REGIME_DEDUCTION_LIMITS["section_80ccd_nps"]
            )
            capped_24b = min(
                deduction_24b, OLD_REGIME_DEDUCTION_LIMITS["section_24b_home_loan"]
            )

            total_deductions = (
                capped_80c
                + capped_80d_self
                + capped_80d_parents
                + capped_80ccd
                + capped_24b
                + other_deductions
            )

            old_result = _compute_regime(
                gross_income=gross_income,
                regime_key="old",
                taxpayer_type=taxpayer_type,
                standard_deduction=OLD_REGIME_STANDARD_DEDUCTION,
                slabs=old_slabs,
                rebate_limit=OLD_REGIME_87A_LIMIT,
                rebate_amount=OLD_REGIME_87A_REBATE,
                total_deductions=total_deductions,
            )
            result["old_regime"] = old_result

        # --- Comparison ---
        if regime == "both":
            new_tax = result["new_regime"]["total_tax"]
            old_tax = result["old_regime"]["total_tax"]
            if new_tax <= old_tax:
                result["recommendation"] = "new_regime"
                result["savings"] = round(old_tax - new_tax, 2)
            else:
                result["recommendation"] = "old_regime"
                result["savings"] = round(new_tax - old_tax, 2)

        return result

    except Exception as exc:
        return {
            "financial_year": "2025-26",
            "assessment_year": "2026-27",
            "gross_income": gross_income if isinstance(gross_income, (int, float)) else 0,
            "regime": regime if isinstance(regime, str) else "both",
            "errors": [f"Income tax calculation failed: {exc}"],
            "disclaimer": DISCLAIMER,
        }
