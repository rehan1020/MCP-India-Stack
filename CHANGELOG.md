# Changelog

## [0.4.2] - 2026-05-31

### Bug Fixes (Round 2 — Deep Code Audit)

- **Capital Gains** — Asset-type-specific LTCG holding period thresholds:
  equity 12mo, real estate 24mo, gold/debentures 36mo, crypto always flat 30%.
  STCG on real estate and gold now correctly noted as slab-rate (not flat rate).
- **EPF/ESIC** — Employee EPF deduction now correctly capped at ₹15,000 wage
  ceiling (statutory). Added `voluntary_pf_on_actual` flag for VPF on full salary.
- **HRA** — Removed Bangalore, Hyderabad, Pune from metro cities list.
  Only Delhi, Mumbai, Chennai, Kolkata qualify for 50% HRA under Section 10(13A).
  Added `_classify_city()` helper with warnings for commonly confused cities.
- **Presumptive Tax** — Full 7-slab new regime and 4-slab old regime via reusable
  `_compute_slab_tax()`. Added Section 87A rebate. Previously only covered 3 slabs.
- **GST Late Fee** — GSTR9 cap (0.25% of turnover) now enforced. Nil return daily
  fee corrected from ₹25 to ₹20 per GST Council notification.
- **Income Tax Interest** — Section 234C shortfall now uses cumulative paid vs
  cumulative required (not single-quarter paid). Fixed incorrect interest calc.
- **Advance Tax** — Installment schedule now shows both `cumulative_amount` and
  `installment_amount` (incremental). The `amount` field returns the quarterly
  payment due, not the confusing cumulative total.
- **Salary Restructuring** — Removed obsolete ₹19,200 conveyance exemption
  (abolished FY2018-19). Standard deduction (₹75,000 new / ₹50,000 old) properly
  shown. Removed stale medical reimbursement line.

### Tests
- Added 30+ regression tests covering all 8 fixed scenarios
- Coverage maintained at 93%+



## [0.4.0] - 2026-05-08

### Security Fix
- `validate_aadhaar` — Now masks full Aadhaar number in output, returns only last 4 digits

### TDS Enhancement
- Added `aggregate_payments_ytd` parameter for 194C aggregate threshold tracking
- Added `payee_type` parameter ("individual_huf" or "other") for 194C rate determination
- Added new sections: 194R (perquisite), 194S (VDA/crypto), 194M (contractor without TAN)

### GST Calculator Enhancement
- Added optional `hsn_code` parameter to look up GST rate from HSN/SAC code
- Added `rate_source` field ("explicit" or "hsn_lookup") in response

### Capital Gains Enhancement
- Added `reinvestment_amount` parameter for Section 54/54F exemption calculation
- Added `section_54_exemption_claimed`, `section_54f_exemption_claimed` fields

### New Tools (35+ total)
- `calculate_epf_esic` — EPF/ESIC contribution calculator
- `calculate_emi` — Loan EMI with amortization schedule
- `calculate_gratuity` — Payment of Gratuity Act calculator
- `calculate_ppf_maturity` — PPF maturity projections
- `bulk_validate_aadhaar` — Parallel Aadhaar validation
- `build_aa_consent_request` — AA consent request builder
- `validate_aa_consent_artifact` — AA consent artifact validator
- `decode_aa_fi_type` — AA FI type decoder
- `calculate_fd_maturity` — Fixed Deposit calculator
- `calculate_rd_maturity` — Recurring Deposit calculator
- `calculate_sip_returns` — SIP returns calculator
- `calculate_step_up_sip` — Step-up SIP calculator
- `calculate_nps_projection` — NPS corpus/pension projection
- `calculate_sukanya_samriddhi` — SSY/SCSS calculator
- `calculate_home_vs_rent` — Buy vs rent comparison
- `calculate_gst_late_fee` — GST late filing penalty
- `calculate_income_tax_interest` — Sections 234A/B/C interest
- `calculate_presumptive_tax` — 44AD/44ADA presumptive tax
- `calculate_professional_tax` — State-wise professional tax
- `calculate_leave_encashment_tax` — Section 10(10AA) leave encashment
- `validate_tan` — TAN validator
- `validate_mobile_number` — Mobile number with operator detection
- `validate_pran` — PRAN validator
- `validate_llpin` — LLPIN validator
- `decode_isin` — ISIN decoder with Luhn check
- `calculate_neft_rtgs_imps_charges` — Bank transaction charges
- `get_regulatory_deadlines` — FY2025-26 tax & regulatory compliance calendar
- `calculate_salary_restructuring` — Salary restructuring tax optimizer

### Tests
- Added test files for new tools
- Coverage: 93%+

## [0.3.0] - 2026-04-28

### Added
- Bulk validation tools for GSTIN, PAN, and IFSC
- HRA, capital gains, and advance tax calculators
- BBPS biller lookup and bank master lookup
- FSSAI, EPF, ESIC, and DigiLocker validation utilities
- Prompt workflows for vendor KYC, salary planning, and invoice audit
- `india://status` and `india://changelog` MCP resources
- Expanded the public tool catalog to 30 tools

### Changed
- Synced package metadata, launch docs, and server card with the 0.3.0 release

## [0.2.0] - 2026-03-26

### Added
- `validate_aadhaar` — Verhoeff checksum validator for 12-digit Aadhaar numbers
- `validate_voter_id` — EPIC format validator with legacy format detection
- `validate_driving_license` — DL format validator with state decode
- `validate_passport` — Indian passport number format validator
- `validate_cin` — Company Identification Number validator with full field decode
- `validate_din` — Director Identification Number format validator
- `calculate_income_tax` — Old vs new regime comparison for FY2025-26
- `calculate_tds` — TDS rate lookup and computation for 10+ sections (FY2025-26)
- `calculate_gst` — GST breakdown calculator (CGST/SGST/IGST/cess)
- `calculate_surcharge` — Surcharge and marginal relief calculator
- External dataset hosting via jsDelivr CDN with background auto-update
- Local dataset caching via platformdirs
- `mcp-india-stack --refresh-all` CLI flag for manual dataset refresh
- `MCP_INDIA_STACK_NO_AUTO_UPDATE` environment variable to disable auto-update

### Changed
- Dataset loader now uses cached files when available and not stale
- Tool responses include cache freshness warnings when applicable

### Dependencies
- Added `platformdirs>=4.0.0`

## [0.1.1] - 2026-03-22

- Fix: Replace SAC-only HSN dataset (681 rows) with full HSN + SAC master
	from services.gst.gov.in (22,471 rows). Goods codes now correctly resolved.

## [0.1.0] - 2026-03-21

- Initial monolith release with 7 tools: IFSC, GSTIN, PAN, UPI VPA, pincode, HSN/SAC, state code
- Offline-first loaders with lazy caching and indexed lookups
- Bundled static datasets and refresh script with validation + checksums
- FastMCP tool wrappers with structured response envelope
- Unit and protocol tests with CI matrix (3.10/3.11/3.12)
