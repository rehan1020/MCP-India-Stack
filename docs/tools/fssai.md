# validate_fssai

Validates a 14-digit FSSAI license number and decodes the embedded state, year, and license type.

**Input:** `license_number` (str) — 14-digit FSSAI license number. Spaces and dashes are ignored.

**Output:** `valid`, `license_number`, `normalized_input`, `state_code`, `state_name`, `license_year`, `license_type_code`, `license_type`, `sequence_number`, `errors`, `warnings`.

**Example prompt:** "Validate FSSAI license number 10019000000001"

**Limitations:** Format validation and decoding only. It does not verify whether the license is currently active on the FSSAI portal.
