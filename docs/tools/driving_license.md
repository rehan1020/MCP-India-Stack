# validate_driving_license

Validates an Indian driving license number format and decodes state code, RTO code, year of issue, and serial number. Standard post-Sarathi format: 2-letter state + 2-digit RTO + 4-digit year + 7-digit serial (15 chars). Handles non-standard/pre-Sarathi formats gracefully.

**Input:** `dl_number` (str) — DL number, 15 chars standard.

**Output:** `valid`, `dl_number`, `state_code`, `state_name`, `rto_code`, `year_of_issue`, `serial`, `errors`, `disclaimer`.

**Example prompt:** "Validate DL number MH0220191234567"

**Limitations:** Format validation only. Cannot verify license validity or status with transport authority.
