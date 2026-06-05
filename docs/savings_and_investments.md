# Savings and Investments

## calculate_epf_esic

Calculate EPF and ESIC contributions for employer and employee. Use when computing payroll costs, employee deductions, or comparing CTC structures across different salary levels.

**Input:**
- `basic_wages` (float): Basic salary + DA per month in INR.
- `gross_wages` (float): Total gross monthly salary in INR.
- `include_employer_share` (bool): If True, return employer costs (default: True).

**Output:** `basic_wages`, `gross_wages`, `epf_breakdown`, `esic_breakdown`, `totals`, `errors`.

**Example prompt:** "Calculate EPF and ESIC for a basic wage of 15000 and gross of 25000."

**Limitations:** EPF ceiling is ₹15,000/month for statutory computation. ESIC applicable when gross wages ≤ ₹21,000/month.


---

## calculate_emi

Calculate EMI for a loan with year-by-year amortization schedule. Use when computing loan EMIs, comparing loan options, or planning prepayment strategies.

**Input:**
- `principal` (float): Loan amount in INR.
- `annual_interest_rate` (float): Annual rate as percentage (e.g., 8.5).
- `tenure_months` (int): Loan tenure in months (max 360).
- `loan_type` (str): Label for the loan type (home, personal, car, education, other).

**Output:** `principal`, `annual_interest_rate`, `tenure_months`, `loan_type`, `emi`, `total_payment`, `total_interest`, `amortization_yearly`, `errors`.

**Example prompt:** "Calculate EMI for a home loan of 50 Lakhs at 8.5% for 20 years."

**Limitations:** Uses standard reducing balance formula. Actual EMI may vary by lender.


---

## calculate_gratuity

Calculate gratuity under the Payment of Gratuity Act, 1972. Use when computing terminal benefits, comparing CTC packages, or planning retirement benefits.

**Input:**
- `last_drawn_salary` (float): Last basic salary + DA per month in INR.
- `years_of_service` (float): Total years served (e.g., 5.8 = 5 yrs 9 months).
- `is_covered_under_act` (bool): True if establishment has 10+ employees.

**Output:** `last_drawn_salary`, `years_of_service`, `completed_years_for_calculation`, `is_covered_under_act`, `gratuity_amount`, `tax_exempt_limit`, `taxable_gratuity`, `minimum_service_met`, `formula_used`.

**Example prompt:** "Calculate gratuity for 6.5 years of service with last drawn salary of 45000."

**Limitations:** Minimum 5 years service required (except death/disablement). Tax-exempt ceiling is ₹20,00,000.


---

## calculate_ppf_maturity

Calculate PPF maturity amount with year-by-year breakdown. Use when planning long-term savings, comparing investment options, or calculating retirement corpus.

**Input:**
- `annual_investment` (float): Amount invested per year in INR (max ₹1,50,000).
- `tenure_years` (int): PPF tenure in years (15, 20, 25, or 30).
- `annual_interest_rate` (float): Annual interest rate percentage (default 7.1).

**Output:** `annual_investment`, `tenure_years`, `annual_interest_rate`, `total_invested`, `maturity_amount`, `total_interest_earned`, `yearly_breakdown`.

**Example prompt:** "Calculate PPF maturity for ₹1,50,000 annual investment for 15 years."

**Limitations:** EEE tax status: exempt at investment, accumulation, and maturity. Rate is government-administered and revised quarterly.


---

## calculate_fd_maturity

Calculate Fixed Deposit (FD) maturity amount. Use when planning short to medium-term secure investments.

**Input:**
- `principal` (float): Initial deposit amount in INR.
- `annual_interest_rate` (float): Annual interest rate percentage.
- `tenure_months` (int): Duration of the fixed deposit in months.
- `compounding_frequency` (str): 'quarterly', 'half-yearly', 'yearly', or 'monthly'.

**Output:** `principal`, `annual_interest_rate`, `tenure_months`, `compounding_frequency`, `maturity_amount`, `total_interest_earned`.

**Example prompt:** "Calculate FD maturity for ₹1,00,000 at 6.5% for 12 months compounded quarterly."

**Limitations:** Pre-mature withdrawal penalties and TDS deductions are not accounted for.


---

## calculate_rd_maturity

Calculate Recurring Deposit maturity amount. Use when projecting RD returns or planning recurring deposits.

**Input:**
- `monthly_installment` (float): Monthly deposit amount in INR.
- `annual_interest_rate` (float): Annual interest rate as percentage.
- `tenure_months` (int): Deposit tenure in months.

**Output:** `monthly_installment`, `annual_interest_rate`, `tenure_months`, `maturity_amount`, `total_interest_earned`.

**Example prompt:** "Calculate RD maturity for ₹5000 monthly at 6.8% for 24 months."


---

## calculate_sip_returns

Calculate SIP maturity with inflation-adjusted returns. Use when projecting mutual fund SIP returns or planning systematic investments.

**Input:**
- `monthly_investment` (float): Monthly SIP amount in INR.
- `expected_annual_return` (float): Expected CAGR as percentage.
- `tenure_years` (int): Investment tenure in years.
- `inflation_rate` (float): Expected inflation rate percentage (default: 6.0).

**Output:** `monthly_investment`, `expected_annual_return`, `tenure_years`, `inflation_rate`, `expected_corpus`, `inflation_adjusted_corpus`, `wealth_gained`.

**Example prompt:** "Calculate SIP returns for ₹10000 monthly at 12% for 10 years."


---

## calculate_step_up_sip

Calculate SIP with annual step-up increment. Use when comparing step-up SIP vs flat SIP or planning salary-linked investments.

**Input:**
- `initial_monthly_investment` (float): Starting SIP amount in INR.
- `annual_step_up_percent` (float): Annual step-up percentage.
- `expected_annual_return` (float): Expected CAGR as percentage.
- `tenure_years` (int): Investment tenure in years.

**Output:** `initial_monthly_investment`, `annual_step_up_percent`, `expected_annual_return`, `tenure_years`, `step_up_corpus`, `flat_sip_corpus`.

**Example prompt:** "Calculate step-up SIP with ₹5000 starting amount, increasing by 10% annually at 12% return for 15 years."


---

## calculate_nps_projection

Calculate NPS corpus and monthly pension at retirement. Use when planning retirement with NPS or projecting pension.

**Input:**
- `monthly_contribution` (float): Monthly NPS contribution in INR.
- `current_age` (int): Current age.
- `retirement_age` (int): Retirement age (default 60).
- `expected_annual_return` (float): Expected annual return percentage (default 10.0).
- `annuity_rate` (float): Annuity rate percentage (default 6.0).
- `annuity_percent` (float): Corpus for annuity (min 40%) (default 40.0).

**Output:** `monthly_contribution`, `current_age`, `retirement_age`, `projected_corpus`, `lump_sum_withdrawal`, `monthly_pension`.

**Example prompt:** "Project NPS corpus for ₹5000 monthly contribution starting at age 30."


---

## calculate_sukanya_samriddhi

Calculate SSY or SCSS maturity amount. Use when planning long-term savings for girl child (SSY) or retirement (SCSS).

**Input:**
- `scheme` (str): 'ssy' for Sukanya Samriddhi or 'scss' for Senior Citizen Savings Scheme.
- `annual_investment` (float): Annual deposit amount in INR.
- `annual_interest_rate` (float): Interest rate as percentage (default 8.2).

**Output:** `scheme`, `annual_investment`, `annual_interest_rate`, `maturity_amount`, `interest_breakdown`, `tax_status`.

**Example prompt:** "Calculate SSY maturity for ₹1,50,000 annual investment."


---

## calculate_home_vs_rent

Compare buying vs renting financial outcome. Use when deciding between buying a home or renting.

**Input:**
- `home_price` (float): Property price in INR.
- `down_payment_percent` (float): Down payment as percentage (default 20.0).
- `loan_interest_rate` (float): Home loan interest rate percentage (default 8.5).
- `loan_tenure_years` (int): Loan tenure in years (default 20).
- `monthly_rent` (float): Current monthly rent in INR (default 25000).
- `annual_rent_increase` (float): Expected rent increase percentage/year (default 5.0).
- `expected_property_appreciation` (float): Property appreciation percentage/year (default 6.0).
- `investment_return` (float): Return on invested down payment percentage (default 12.0).
- `analysis_years` (int): Years to compare (default 20).

**Output:** `buy_rent_comparison`, `yearly_breakdown`, `break_even_analysis`.

**Example prompt:** "Should I buy a home for 80 Lakhs or rent for ₹25000/month?"


---

## calculate_leave_encashment_tax

Calculate tax-exempt portion of leave encashment under Section 10(10AA). Use when computing leave encashment tax exemption or planning retirement benefits.

**Input:**
- `leave_encashment_amount` (float): Actual amount received in INR.
- `average_monthly_salary` (float): Average of last 10 months basic + DA.
- `earned_leave_balance_days` (int): Days of earned leave.
- `years_of_service` (int): Total years of service.
- `is_government_employee` (bool): Government employee flag (default False).

**Output:** `leave_encashment_amount`, `exemption_amount`, `taxable_portion_breakdown`.

**Example prompt:** "Calculate leave encashment exemption for 300,000 received after 15 years of service."


---

