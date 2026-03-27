# validate_din

Validates an Indian DIN (Director Identification Number). Exactly 8 digits. Zero-pads shorter input.

**Input:** `din` (str) — 8-digit DIN.

**Output:** `valid`, `din` (normalized), `errors`, `disclaimer`.

**Example prompt:** "Validate DIN 00012345"

**Limitations:** Format validation only. Cannot verify director status with MCA.
