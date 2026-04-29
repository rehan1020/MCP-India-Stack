# vendor_kyc

A workflow prompt for GSTIN, PAN, and IFSC verification during vendor onboarding.

**Use case:** validate a vendor in three steps: `validate_gstin`, `validate_pan`, and `lookup_ifsc`.

**Example prompt:** "Run vendor KYC for GSTIN 27AAPFU0939F1ZV, PAN AAPFU0939F, and IFSC HDFC0000001"

**Notes:** This is a prompt workflow, not a callable tool. It is meant to guide an MCP client or agent through the verification sequence.
