# calculate_advance_tax

Calculates the quarterly advance tax schedule for an estimated annual income.

**Input:** `estimated_income` (float), `regime` (str), `taxpayer_type` (str), `existing_tds` (float).

**Output:** `total_tax_liability`, `existing_tds`, `net_tax_liability`, `advance_tax_due`, `regime`, `taxpayer_type`, `is_advance_tax_required`, `installments`, `interest_rules`, `errors`, `warnings`.

**Example prompt:** "Estimate advance tax installments for 24 lakh annual income under the new regime"

**Limitations:** Estimates current-year liability from the input assumptions. It does not know your full tax profile.
