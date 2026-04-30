# GSTIN Tools

## validate_gstin

Validates GSTIN structure and checksum, decodes state/PAN/entity metadata, and reports category limitations for special classes. Validates structure and checksum only; does not verify active GSTN registration status.

**Input:** `gstin` (str) — 15-character GSTIN. Example: `27AAPFU0939F1ZV`.

**Output:** `valid`, `gstin`, `state_code`, `state_name`, `pan`, `entity_number`, `checksum_digit`, `checksum_valid`, `category`, `errors`, `warnings`.

**Example prompt:** "Validate GSTIN 27AAPFU0939F1ZV"

**Limitations:** Validates format and checksum only. Cannot verify if the GSTIN is currently active or cancelled on the GST portal.

---

## bulk_validate_gstin

Validate multiple GSTINs in parallel using a thread pool. Maximum 500 GSTINs per call.

**Input:** `gstins` (list[str]) — List of GSTIN strings to validate.

**Output:** `results` (list of single validation outputs), `total`, `valid_count`, `invalid_count`.

**Example prompt:** "Validate these GSTINs in bulk: 27AAPFU0939F1ZV, 27AAPFU0939F1ZW"
