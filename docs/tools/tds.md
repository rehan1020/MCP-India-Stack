# calculate_tds

Calculates TDS (Tax Deducted at Source) for FY2025-26 across 12+ sections. Handles threshold checks, PAN/no-PAN rate differences, and senior citizen exceptions.

**Inputs:** `section` (TDS section key), `payment_amount`, `pan_available`, `is_senior_citizen`.

**Output:** `tds_applicable`, `rate_applied`, `tds_amount`, `net_payment`, `no_pan_surcharge`, `threshold`, `disclaimer`.

**Supported sections:** 194C (individual/company), 194J (professional/technical), 194A (bank/other), 194H, 194I (land/plant), 194Q, 194B, 194D.

**Example prompt:** "What TDS applies on ₹1 lakh professional fees payment?"

**Limitations:** General FY2025-26 rates. DTAA provisions, Form 15G/15H, and specific exemptions not included.
