# validate_pan

Validates Indian PAN format and decodes entity type from the 4th character. Structural validation only.

**Input:** `pan` (str) — 10-character PAN string. Example: `AAAPL1234C`.

**Output:** `valid`, `pan`, `entity_type_code`, `entity_type`, `pan_type`, `is_individual`, `serial_number`, `check_digit`, `errors`.

**Example prompt:** "Validate PAN AAAPL1234C"

**Limitations:** PAN check character (10th digit) is not publicly algorithmic. This tool validates the 4th character entity type and overall digit/letter structure. Cannot verify if the PAN is valid with IT Department.

