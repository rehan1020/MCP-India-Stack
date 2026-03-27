# lookup_ifsc

Validates IFSC format and returns bank branch metadata from bundled dataset with optional live fallback to Razorpay IFSC API.

**Input:** `ifsc_code` (str) — 11-character IFSC code. Case-insensitive. Example: `HDFC0000001`.

**Output:** `found`, `ifsc`, `bank`, `branch`, `address`, `city`, `district`, `state`, `contact`, `upi` (bool), `rtgs` (bool), `neft` (bool), `imps` (bool), `source`.

**Example prompt:** "Get branch details for IFSC ICIC0000001"

**Limitations:** Bundled data may be slightly behind newest branch openings. Live fallback requires internet connectivity.

