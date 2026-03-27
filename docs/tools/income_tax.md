# calculate_income_tax

Calculates Indian income tax for FY2025-26 under old regime, new regime, or both for comparison. Includes slab computation, standard deduction, Section 87A rebate, surcharge with marginal relief, and 4% health & education cess.

**Inputs:** `gross_income`, `regime` (new/old/both), `taxpayer_type`, optional old-regime deductions (80C, 80D, 80CCD, 24b, other).

**Output:** Per-regime breakdown with `taxable_income`, `base_tax`, `rebate_87a`, `surcharge`, `cess`, `total_tax`, `effective_rate`, `monthly_tax`, `take_home_annual`. Comparison mode adds `recommendation` and `savings`.

**Example prompt:** "Compare income tax for ₹15 lakh salary under both regimes"

**Limitations:** FY2025-26 rates only. Estimate — consult a CA for actual filing. Does not handle HRA, LTA, or other specific exemptions.
