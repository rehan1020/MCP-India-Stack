# Tax and Financial Calculators

## calculate_income_tax

Calculates Indian income tax for FY2025-26 under old regime, new regime, or both for comparison. Includes slab computation, standard deduction, Section 87A rebate, surcharge with marginal relief, and 4% health & education cess.

**Inputs:** `gross_income`, `regime` (new/old/both), `taxpayer_type`, optional old-regime deductions (80C, 80D, 80CCD, 24b, other).

**Output:** Per-regime breakdown with `taxable_income`, `base_tax`, `rebate_87a`, `surcharge`, `cess`, `total_tax`, `effective_rate`, `monthly_tax`, `take_home_annual`. Comparison mode adds `recommendation` and `savings`.

**Example prompt:** "Compare income tax for ₹15 lakh salary under both regimes"

**Limitations:** FY2025-26 rates only. Estimate — consult a CA for actual filing. Does not handle HRA, LTA, or other specific exemptions.


---

## calculate_tds

Calculates TDS (Tax Deducted at Source) for FY2025-26 across 12+ sections. Handles threshold checks, PAN/no-PAN rate differences, and senior citizen exceptions.

**Inputs:** `section` (TDS section key), `payment_amount`, `pan_available`, `is_senior_citizen`.

**Output:** `tds_applicable`, `rate_applied`, `tds_amount`, `net_payment`, `no_pan_surcharge`, `threshold`, `disclaimer`.

**Supported sections:** 194C (individual/company), 194J (professional/technical), 194A (bank/other), 194H, 194I (land/plant), 194Q, 194B, 194D.

**Example prompt:** "What TDS applies on ₹1 lakh professional fees payment?"

**Limitations:** General FY2025-26 rates. DTAA provisions, Form 15G/15H, and specific exemptions not included.


---

## calculate_gst

Calculates GST breakdown with CGST/SGST/IGST split and optional cess. Supports all valid GST rates and both intra-state and inter-state transactions. Can back-calculate base from GST-inclusive amounts.

**Inputs:** `amount`, `gst_rate` (0/0.1/0.25/1.5/3/5/12/18/28), `transaction_type` (intra_state/inter_state), `amount_includes_gst`, `cess_category`.

**Output:** `base_amount`, `cgst_rate/amount`, `sgst_rate/amount`, `igst_rate/amount`, `cess_rate/amount`, `total_gst`, `total_amount`, `disclaimer`.

**Example prompt:** "Calculate 18% GST on ₹10,000 for an intra-state sale"

**Limitations:** Rates are for general reference. Actual HSN/SAC classification may vary by notifications.


---

## calculate_surcharge

Calculates surcharge and marginal relief on income tax for FY2025-26. Standalone version of the surcharge logic used internally by `calculate_income_tax`.

**Inputs:** `total_income`, `base_tax`, `regime` (new/old).

**Output:** `surcharge_rate`, `surcharge_before_relief`, `marginal_relief`, `surcharge_after_relief`, `cess_base`, `disclaimer`.

**Example prompt:** "What surcharge applies on ₹60 lakh income with ₹15 lakh base tax?"

**Limitations:** FY2025-26 rates. New regime caps surcharge at 25%. Old regime allows up to 37%.


---

## calculate_hra_exemption

Calculates House Rent Allowance (HRA) exemption under Section 10(13A) using salary, rent, and city-type rules.

**Input:** `basic_salary` (float), `hra_received` (float), `rent_paid` (float), `city_type` (str), `is_government_employee` (bool).

**Output:** `exemption`, `taxable_hra`, `annual_basic_salary`, `annual_hra_received`, `annual_rent_paid`, `breakdown`, `errors`, `warnings`.

**Example prompt:** "Calculate HRA exemption for a non-metro employee with 50,000 monthly basic, 2,40,000 HRA, and 1,80,000 annual rent"

**Limitations:** Uses the standard exemption formula only. It is a tax estimate and not filing advice.


---

## calculate_capital_gains

Calculates capital gains tax for equity, mutual funds, real estate, gold, debentures, and crypto.

**Input:** `sale_price` (float), `purchase_price` (float), `asset_type` (str), `holding_period_days` (int), `inflation_index_purchase` (float | null), `inflation_index_sale` (float | null), `expenses_on_sale` (float), `improvements` (float).

**Output:** `short_term_gains`, `long_term_gains`, `total_gains`, `is_long_term`, `holding_period_days`, `tax_liability`, `asset_type`, `stcg_rate`, `ltcg_rate`, `cost_inflation_adjusted`, `exemption_threshold`, `errors`, `warnings`.

**Example prompt:** "Calculate capital gains on sale of equity shares held for 500 days"

**Limitations:** Tax treatment varies by asset class and notification date. Use this as an estimate only.


---

## calculate_advance_tax

Calculates the quarterly advance tax schedule for an estimated annual income.

**Input:** `estimated_income` (float), `regime` (str), `taxpayer_type` (str), `existing_tds` (float).

**Output:** `total_tax_liability`, `existing_tds`, `net_tax_liability`, `advance_tax_due`, `regime`, `taxpayer_type`, `is_advance_tax_required`, `installments`, `interest_rules`, `errors`, `warnings`.

**Example prompt:** "Estimate advance tax installments for 24 lakh annual income under the new regime"

**Limitations:** Estimates current-year liability from the input assumptions. It does not know your full tax profile.


---

## calculate_gst_late_fee

Calculate GST late filing penalty. Use when estimating late filing fees or planning compliance.

**Input:**
- `return_type` (str): 'GSTR1', 'GSTR3B', or 'GSTR9'.
- `days_delayed` (int): Number of days delayed.
- `annual_turnover` (float): Annual turnover in INR for cap calculation.
- `has_nil_liability` (bool): True if nil return (default False).

**Output:** `return_type`, `days_delayed`, `annual_turnover`, `has_nil_liability`, `late_fee_breakdown`.

**Example prompt:** "Calculate GST late fee for GSTR3B delayed by 15 days with 10 Lakhs turnover."


---

## calculate_income_tax_interest

Calculate interest under Sections 234A, 234B, 234C. Use when computing penalty interest for late tax filing or short advance tax payments.

**Input:**
- `total_tax_liability` (float): Total tax liability in INR.
- `tds_deducted` (float): TDS already deducted in INR (default 0.0).
- `advance_tax_paid` (dict): Dict with q1, q2, q3, q4 quarterly payments.
- `filing_date` (str): Filing date YYYY-MM-DD or null if not filed.
- `due_date` (str): Due date YYYY-MM-DD (default '2025-07-31').

**Output:** `total_tax_liability`, `interest_breakdown`.

**Example prompt:** "Calculate tax interest for liability of ₹100,000 filed on 2025-10-15."


---

## calculate_presumptive_tax

Calculate tax under presumptive scheme (Sections 44AD, 44ADA). Use when computing tax for small businesses or professionals under presumptive taxation.

**Input:**
- `scheme` (str): '44AD' for business or '44ADA' for professionals.
- `gross_receipts` (float): Total gross receipts in INR.
- `digital_receipt_percent` (float): Percentage via digital mode (default 100.0).
- `regime` (str): 'new' or 'old' tax regime (default 'new').
- `age` (int): Assessee age (default 35).
- `deductions_80c` (float): Section 80C deductions for old regime (default 0).

**Output:** `scheme`, `gross_receipts`, `presumptive_income`, `total_tax_payable`.

**Example prompt:** "Calculate presumptive tax for a professional earning 45 Lakhs via 44ADA."


---

## get_regulatory_deadlines

Get India's tax & regulatory compliance calendar for FY2025-26. Use when planning tax compliance schedules, setting reminders for deadlines, or building financial compliance dashboards.

**Input:**
- `category` (str): Filter by category (Income Tax, TDS, GST, PF/ESIC, ROC, etc.)
- `from_date` (str): Start date filter (YYYY-MM-DD).
- `to_date` (str): End date filter (YYYY-MM-DD).

**Output:** `deadlines` (list of matching deadlines with descriptions and dates).

**Example prompt:** "What are the regulatory deadlines for Income Tax in July 2025?"

**Limitations:** Deadlines can be extended by the government. Always cross-verify.


---

## calculate_professional_tax

Calculate state-wise professional tax. Use when computing total tax liability including professional tax deductions.

**Input:**
- `gross_salary_monthly` (float): Monthly gross salary in INR.
- `state_code` (str): 2-char state code (e.g., 'MH', 'KA', 'TN').

**Output:** `gross_salary_monthly`, `state_code`, `applicable`, `monthly_tax`, `annual_tax`.

**Example prompt:** "Calculate professional tax in MH for a salary of 50000."


---

## calculate_salary_restructuring

Calculate salary restructuring options for tax optimization. Use when advising employees on tax-efficient salary structures, comparing restructuring options, or planning CTC optimization.

**Input:**
- `current_gross` (float): Current gross annual salary in INR.
- `current_basic_ratio` (float): Current basic salary as ratio of gross (default 0.50).
- `structure_type` (str): Structure option ('standard', 'optimized', or 'startup').
- `include_meal_card` (bool): Include Sodexo/Food card allowance (default False).
- `include_wallet_allowance` (bool): Include flexible wallet allowance (default False).
- `has_hra` (bool): Employee receives HRA (default True).
- `rent_in_metro` (bool): Rent paid in metro city for higher HRA (default False).
- `family_medical` (bool): Include family medical insurance (default False).
- `parents_medical` (bool): Include parents medical insurance (default False).

**Output:** `structure`, `deductions`, `estimated_tax`, `take_home_salary`.

**Example prompt:** "Optimize a CTC of 25 Lakhs for a non-metro employee with standard options."


---

