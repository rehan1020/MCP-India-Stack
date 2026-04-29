# validate_esic_code

Validates an ESIC employer code in the `XX-XXXXX-XXXXX` format.

**Input:** `code` (str) — ESIC employer code.

**Output:** `valid`, `normalized_input`, `regional_code`, `employer_code`, `sub_code`, `errors`, `warnings`.

**Example prompt:** "Validate ESIC code 13-12345-67890"

**Limitations:** Format validation only. It does not check ESIC portal registration.
