# lookup_pincode

Returns all post offices for a pincode with district, state context and mapped GST state code.

**Input:** `pincode` (str) — 6-digit Indian pincode. Spaces/hyphens accepted.

**Output:** `found`, `pincode`, `state`, `state_code`, `district`, `region`, `post_offices` (list of branch names), `count`.

**Example prompt:** "Which post offices fall under pincode 110001?"

**Limitations:** Pincode boundaries can occasionally change. Geocoding is approximate based on centroid of the postal area.

