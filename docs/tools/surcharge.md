# calculate_surcharge

Calculates surcharge and marginal relief on income tax for FY2025-26. Standalone version of the surcharge logic used internally by `calculate_income_tax`.

**Inputs:** `total_income`, `base_tax`, `regime` (new/old).

**Output:** `surcharge_rate`, `surcharge_before_relief`, `marginal_relief`, `surcharge_after_relief`, `cess_base`, `disclaimer`.

**Example prompt:** "What surcharge applies on ₹60 lakh income with ₹15 lakh base tax?"

**Limitations:** FY2025-26 rates. New regime caps surcharge at 25%. Old regime allows up to 37%.
