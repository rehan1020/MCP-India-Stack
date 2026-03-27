# validate_upi_vpa

Validates UPI VPA structure and decodes known provider handles from curated data.

**Input:** `vpa` (str) — UPI virtual payment address. Example: `user@okaxis`.

**Output:** `valid`, `vpa`, `username`, `handle`, `known_provider`, `provider_name`, `bank_name`, `errors`.

**Example prompt:** "Check if user@okaxis is a valid UPI ID"

**Limitations:** Structural validation only. Does not verify if the specific VPA is registered or active on the NPCI network. Unknown handles are not auto-invalidated.

