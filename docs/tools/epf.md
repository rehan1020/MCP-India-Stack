# validate_epf_code

Validates an EPF establishment code in the `XX/XXXXX/XXXXXX/XXX` format.

**Input:** `code` (str) — EPF establishment code.

**Output:** `valid`, `normalized_input`, `region_code`, `office_code`, `establishment_code`, `extension`, `errors`, `warnings`.

**Example prompt:** "Validate EPF code 07/12345/678901/001"

**Limitations:** Format validation only. It does not query EPFO registration status.
