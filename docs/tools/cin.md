# validate_cin

Validates and decodes an Indian CIN (Company Identification Number). 21 characters: listing status (L/U) + 5-digit NIC code + 2-letter state + 4-digit year + 3-letter company type + 6-digit serial.

**Input:** `cin` (str) — 21-character CIN.

**Output:** `valid`, `cin`, `listing_status`, `nic_code`, `state_code`, `state_name`, `year_of_incorporation`, `company_type_code`, `company_type`, `sequential_number`, `errors`.

**Example prompt:** "Decode CIN L17110MH1973PLC019786"

**Limitations:** Format validation with field decoding. No public checksum algorithm. Cannot verify company registration status with MCA.
