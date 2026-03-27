# Changelog

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
