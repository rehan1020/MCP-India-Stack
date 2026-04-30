# PAN Tools

## validate_pan

Validates Indian PAN format and decodes entity type from the 4th character. Structural validation only.

**Input:** `pan` (str) — 10-character PAN string. Example: `AAAPL1234C`.

**Output:** `valid`, `pan`, `entity_type_code`, `entity_type`, `pan_type`, `is_individual`, `serial_number`, `check_digit`, `errors`.

**Example prompt:** "Validate PAN AAAPL1234C"

**Limitations:** PAN check character (10th digit) is not publicly algorithmic. This tool validates the 4th character entity type and overall digit/letter structure. Cannot verify if the PAN is valid with IT Department.

---

## bulk_validate_pan

Validate multiple PANs in parallel. Maximum 500 PANs per call.

**Input:** `pans` (list[str]) — List of 10-character PAN strings.

**Output:** `results` (list of single validation outputs), `total`, `valid_count`.

**Example prompt:** "Bulk validate these PANs: AAAPL1234C, BBBCM5678D"

---

## decode_pan_type

Decodes the PAN entity type from the 4th character and provides KYC routing hints.

**Input:** `pan` (str) — 10-character PAN.

**Output:** `pan`, `entity_type_code`, `entity_type_label`, `kyc_routing_hint`.

**Example prompt:** "What is the entity type for PAN AAAPL1234C?"
