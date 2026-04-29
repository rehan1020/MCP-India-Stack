# lookup_bank

Looks up bank details from the bundled bank master sample by bank name or IFSC prefix.

**Input:** `name_or_code` (str) — bank name or IFSC code prefix.

**Output:** `banks`, `count`.

**Example prompt:** "Look up the bank for IFSC HDFC0000001"

**Limitations:** This is a lightweight bundled lookup. Use `lookup_ifsc` for full branch metadata.
