# Banking and Account Aggregator

## calculate_neft_rtgs_imps_charges

Calculate NEFT/RTGS/IMPS/UPI transaction charges. Use when estimating bank transfer costs or comparing payment modes.

**Input:**
- `transfer_mode` (str): 'NEFT', 'RTGS', 'IMPS', or 'UPI'.
- `amount` (float): Transfer amount in INR.
- `account_type` (str): 'savings' or 'current' (default 'savings').
- `is_online` (bool): True if done via online banking (default True).

**Output:** `transfer_mode`, `amount`, `charge_breakdown`.

**Example prompt:** "What are the charges for a ₹3,00,000 RTGS transfer?"


---

## Account Aggregator (AA) Consent

## build_aa_consent_request

Build AA (Account Aggregator) consent request JSON per ReBIT spec. Use when setting up data sharing consent for open banking workflows.

**Input:**
- `customer_id` (str): AA customer address (e.g., user@onemoney).
- `fi_types` (list[str]): FI types (e.g., DEPOSIT, MUTUAL_FUNDS, INSURANCE).
- `date_range_from` (str): Start date YYYY-MM-DD.
- `date_range_to` (str): End date YYYY-MM-DD.
- `consent_expiry_days` (int): Days until consent expires (default 30).
- `purpose_code` (str): ReBIT purpose code (101-106) (default '101').
- `fetch_type` (str): 'ONETIME' or 'PERIODIC' (default 'ONETIME').
- `frequency_unit` (str): 'HOUR', 'DAY', 'MONTH', 'YEAR' for PERIODIC.
- `frequency_value` (int): Frequency value for PERIODIC.

**Output:** `valid`, `consent_request`, `errors`.

**Example prompt:** "Build AA consent for user@onemoney to fetch DEPOSIT data for the last year."


---

## validate_aa_consent_artifact

Validate AA consent artifact structure and flags. Use when verifying consent artifacts received from AA before processing.

**Input:**
- `artifact` (dict): Consent artifact JSON from AA response.

**Output:** `validated`, `artifact`, `errors`, `warnings`.

**Example prompt:** "Validate this AA consent artifact JSON..."


---

## decode_aa_fi_type

Decode AA Financial Information type and get MCP tool pairings. Use when mapping FI types to validation/calculation tools.

**Input:**
- `fi_type` (str): FI type code (e.g., 'DEPOSIT', 'MUTUAL_FUNDS').

**Output:** `fi_type`, `description`, `fields`, `tool_pairings`.

**Example prompt:** "Decode AA FI type DEPOSIT"


---

