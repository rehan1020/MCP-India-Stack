# validate_voter_id

Validates an Indian Voter ID (EPIC) number format. Standard format: 3 uppercase letters + 7 digits (10 characters). Detects possible legacy EPIC formats issued before 2017 ERONET standardisation.

**Input:** `voter_id` (str) — 10-character EPIC number.

**Output:** `valid`, `epic`, `prefix`, `serial`, `format` (standard/legacy_possible), `errors`, `disclaimer`.

**Example prompt:** "Validate voter ID ABC1234567"

**Limitations:** Format validation only. Cannot verify voter registration status with Election Commission.
