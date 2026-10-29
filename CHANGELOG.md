# Changelog

## [0.7.0] - 2026-10-29

### Refactoring & Core Parity (Update 5b)

- **Inline Tool Extraction**: Extracted the remaining 9 inline registration tools into modular core implementations under `src/mcp_india_stack/tools/`: `bulk_validate_gstin` (`tools/bulk_gstin.py`), `bulk_validate_pan` (`tools/bulk_pan.py`), `bulk_validate_ifsc` (`tools/bulk_ifsc.py`), `decode_pan_type` (`tools/pan_type.py`), `decode_digilocker_uri` (`tools/digilocker.py`), `lookup_bank` (`tools/bank_lookup.py`), `validate_aa_consent_artifact` (`tools/aa_consent.py`), `validate_epf_code` (`tools/epf_code.py`), and `validate_esic_code` (`tools/esic_code.py`).
- **Thin Registration Wrappers**: Reduced all tool wrappers in `src/mcp_india_stack/registrations/*.py` to thin exception-handling delegates ($\le 3$ statements) delegating to core functions, satisfying regression guard G11 with zero non-delegating exceptions.
- **Worker Clamping Consolidation**: Consolidated duplicate `_clamp_bulk_workers` implementations into a single canonical definition in `src/mcp_india_stack/tools/bulk_common.py`, satisfying regression guard G03.
- **100% Core Parity**: Achieved 100% core module function parity across all 78 registered tools with zero parity exclusions. Verified with comprehensive golden output tests (`tests/test_golden_outputs.py`).

### Security & CI Hardening (Update 7)

- **Comprehensive Regression Guards (G01–G20)**: Added suite of architectural and security invariant tests enforcing CORS rules, constant-time auth, worker clamping bounds, dataset integrity, network import restrictions, dead code elimination, telemetry pseudonymization, elevated tool gating, line count bounds, wrapper delegation, single imports, loopback defaults, middleware order, fail-closed startup refusal, host allowlists, rate limiting, and zero-skip/nosec rules.
- **CI Hardening & Pinned Actions**: Pinned all GitHub Actions to exact immutable commit SHAs across CI, Publish, and Security Audit workflows. Added workflow call support, job timeouts, minimal required permissions, and tag-version checks.
- **Automated Security Gates**: Added Bandit SAST scanning and `pip-audit` dependency vulnerability scanning backed by `.pip-audit-ignore.toml` with strict expiry enforcement.
- **Lockfile & Distribution Smoke Testing**: Added automated lockfile drift detection with `uv` and clean-environment wheel installation smoke test.

### Removed (Update 6.7)

- **Runtime Dataset Refresh & Caching**: Removed runtime CDN fetching, background updater threads, cache directory resolution, and staleness logic. All datasets are strictly bundled offline and updated with package releases.
- **CLI `--refresh-all`**: Flag is deprecated and hidden (`help=argparse.SUPPRESS`). Invoking it now outputs a removal notice to stderr and exits with code 2 (breaking for callers relying on `--refresh-all`).

### Security & Network Boundary Completion (Update 6.6)

- **Middleware Ordering**: Hardened middleware stack order to CORS (outermost) -> Auth -> RateLimit (innermost). Preflights succeed without credentials, and 401/429 error responses reliably preserve CORS headers.
- **Brute-Force Authentication Throttling**: Added `MCP_INDIA_STACK_AUTH_FAIL_LIMIT` (default 10) to track failed authentication attempts per host in a bounded, sliding 60-second window, responding with HTTP 429 and `Retry-After`. Valid tokens pass directly and are unaffected by third-party failure state.
- **Key-Hashed Rate Limiting**: Validated requests are rate-limited in a bounded store keyed by the truncated SHA-256 digest of the token (`key:<hash[:16]>`), completely removing raw secret tokens from memory. Unauthenticated requests key by client IP.
- **Fail-Closed Startup Safeguards**: Refuses startup if `MCP_INDIA_STACK_API_KEY` is shorter than 32 characters, or if attempting to bind to a non-loopback interface without an API key (unless explicitly opted-in with `MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK=1`).
- **DNS Rebinding & Transport Security**: Auto-configures `allowed_hosts` and `allowed_origins` in FastMCP transport security using `MCP_INDIA_STACK_ALLOWED_HOSTS`, `MCP_INDIA_STACK_ALLOWED_ORIGINS`, and Render's `RENDER_EXTERNAL_HOSTNAME`.

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
