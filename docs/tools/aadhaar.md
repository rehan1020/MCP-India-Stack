# validate_aadhaar

Validates a 12-digit Indian Aadhaar number using the Verhoeff checksum algorithm. Strips spaces and hyphens, checks first digit (cannot be 0 or 1), and verifies checksum. Format validation only — not connected to UIDAI.

**Input:** `aadhaar` (str) — 12-digit Aadhaar number. Spaces/hyphens accepted.

**Output:** `valid`, `aadhaar`, `formatted` (XXXX XXXX XXXX), `checksum_valid`, `first_digit_valid`, `errors`, `disclaimer`.

**Example prompt:** "Validate this Aadhaar number: 2959 4583 7261"

**Limitations:** Cannot verify identity or active status with UIDAI. Structural and checksum validation only.
