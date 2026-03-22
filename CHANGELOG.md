# Changelog

## [0.1.1] - 2026-03-22

- Fix: Replace SAC-only HSN dataset (681 rows) with full HSN + SAC master
	from services.gst.gov.in (22,471 rows). Goods codes now correctly resolved.

## [0.1.0] - 2026-03-21

- Initial monolith release with 7 tools: IFSC, GSTIN, PAN, UPI VPA, pincode, HSN/SAC, state code
- Offline-first loaders with lazy caching and indexed lookups
- Bundled static datasets and refresh script with validation + checksums
- FastMCP tool wrappers with structured response envelope
- Unit and protocol tests with CI matrix (3.10/3.11/3.12)

