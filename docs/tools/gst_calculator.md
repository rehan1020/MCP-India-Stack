# calculate_gst

Calculates GST breakdown with CGST/SGST/IGST split and optional cess. Supports all valid GST rates and both intra-state and inter-state transactions. Can back-calculate base from GST-inclusive amounts.

**Inputs:** `amount`, `gst_rate` (0/0.1/0.25/1.5/3/5/12/18/28), `transaction_type` (intra_state/inter_state), `amount_includes_gst`, `cess_category`.

**Output:** `base_amount`, `cgst_rate/amount`, `sgst_rate/amount`, `igst_rate/amount`, `cess_rate/amount`, `total_gst`, `total_amount`, `disclaimer`.

**Example prompt:** "Calculate 18% GST on ₹10,000 for an intra-state sale"

**Limitations:** Rates are for general reference. Actual HSN/SAC classification may vary by notifications.
