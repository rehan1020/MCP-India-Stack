# lookup_hsn_code

Supports exact HSN/SAC lookup and keyword search over descriptions. Returns GST rates and classification metadata.

**Inputs:**
- `code` (str, optional) — Exact 2, 4, 6, or 8 digit HSN/SAC code.
- `keyword` (str, optional) — Token to search within descriptions (e.g., "chocolate").

**Output:** `found`, `matches` (list), `query_type`, `count`, `disclaimer`. 
Each match includes `hsn_code`, `description`, `igst`, `cgst`, `sgst`, `compensation_cess`.

**Example prompt:** "Find the GST rate for HSN code 6109" or "Search HSN for 'solar panels'"

**Limitations:** Rates are for general reference and may be subject to specific notifications or conditions. Always verify with official GST Council notifications.

