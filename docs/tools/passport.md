# validate_passport

Validates an Indian passport number format. Format: 1 uppercase letter (series) + 7 digits = 8 characters. No publicly available checksum.

**Input:** `passport_number` (str) — 8-character passport number.

**Output:** `valid`, `passport_number`, `series_letter`, `serial`, `errors`, `disclaimer`.

**Example prompt:** "Is A1234567 a valid Indian passport number?"

**Limitations:** Format validation only. Cannot verify passport validity or status with MEA.
