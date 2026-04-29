# calculate_hra_exemption

Calculates House Rent Allowance (HRA) exemption under Section 10(13A) using salary, rent, and city-type rules.

**Input:** `basic_salary` (float), `hra_received` (float), `rent_paid` (float), `city_type` (str), `is_government_employee` (bool).

**Output:** `exemption`, `taxable_hra`, `annual_basic_salary`, `annual_hra_received`, `annual_rent_paid`, `breakdown`, `errors`, `warnings`.

**Example prompt:** "Calculate HRA exemption for a non-metro employee with 50,000 monthly basic, 2,40,000 HRA, and 1,80,000 annual rent"

**Limitations:** Uses the standard exemption formula only. It is a tax estimate and not filing advice.
