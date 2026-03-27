# decode_state_code

Decodes GST state code metadata from a 2-digit code or GSTIN prefix. Provides canonical state name, abbreviation, capital, and GST zone mapping.

**Input:** `value` (str) — Two-digit code (e.g., `27`) or full GSTIN (e.g., `27AAPFU0939F1ZV`).

**Output:** `found`, `state_code`, `state_name`, `abbreviation`, `capital`, `zone`, `is_ut` (boolean), `notes`.

**Example prompt:** "Decode GST state code 27"

**Limitations:** Static mapping of 37+ states and UTs. Does not verify if a particular GSTIN is currently active.

