# invoice_audit

A workflow prompt for GSTIN, HSN, and GST-rate validation during invoice review.

**Use case:** combine `validate_gstin`, `lookup_hsn_code`, and `calculate_gst` when checking invoice tax correctness.

**Example prompt:** "Audit this invoice GSTIN and HSN classification"

**Notes:** This is a prompt workflow, not a callable tool. It is intended for invoice compliance review and tax checks.
