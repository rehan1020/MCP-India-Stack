# lookup_bbps_biller

Looks up BBPS biller entries from the bundled offline biller directory.

**Input:** `category` (str | null), `state` (str | null), `biller_id` (str | null).

**Output:** `found`, `billers`, `count`, plus matching biller metadata and supported parameters.

**Example prompt:** "Find BBPS electricity billers in Maharashtra"

**Limitations:** Offline biller directory only. For the live NPCI directory, use the official BBPS systems.
