# validate_gstin

Validates GSTIN structure and checksum, decodes state/PAN/entity metadata, and reports category limitations for special classes. Validates structure and checksum only; does not verify active GSTN registration status.

**Input:** `gstin` (str) — 15-character GSTIN. Example: `27AAPFU0939F1ZV`.

**Output:** `valid`, `gstin`, `state_code`, `state_name`, `pan`, `entity_number`, `checksum_digit`, `checksum_valid`, `category`, `errors`, `warnings`.

**Example prompt:** "Validate GSTIN 27AAPFU0939F1ZV"

**Limitations:** Validates format and checksum only. Cannot verify if the GSTIN is currently active or cancelled on the GST portal.

