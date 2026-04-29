# decode_digilocker_uri

Decodes a DigiLocker URI and maps it to the best matching validator.

**Input:** `uri` (str) — DigiLocker URI starting with `dlg://`.

**Output:** `uri`, `issuer`, `document_type`, `expected_fields`, `verification_pairing`, `normalized_input`, `errors`, `warnings`.

**Example prompt:** "Decode DigiLocker URI dlg://uidai/aadhaar/123456789012"

**Limitations:** This only parses and maps the URI. It does not verify the document with DigiLocker itself.
