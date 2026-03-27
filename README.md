# mcp-india-stack

[![PyPI version](https://img.shields.io/pypi/v/mcp-india-stack.svg)](https://pypi.org/project/mcp-india-stack/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml)

MCP server exposing Indian financial and government APIs for AI agents. Zero auth. Offline-first.

## Install

```bash
pip install mcp-india-stack
```

## Run

```bash
mcp-india-stack
```

or

```bash
python -m mcp_india_stack
```

## Tools

### Lookup Tools
- [`lookup_ifsc`](docs/tools/ifsc.md) — Bank branch details from IFSC code
- [`lookup_pincode`](docs/tools/pincode.md) — India pincode details and post offices
- [`lookup_hsn_code`](docs/tools/hsn.md) — HSN/SAC code lookup by code or keyword
- [`decode_state_code`](docs/tools/state_code.md) — GST state code metadata

### Validation Tools
- [`validate_gstin`](docs/tools/gstin.md) — GSTIN structure and checksum
- [`validate_pan`](docs/tools/pan.md) — PAN format and entity type decode
- [`validate_upi_vpa`](docs/tools/upi.md) — UPI VPA structure and provider decode
- [`validate_aadhaar`](docs/tools/aadhaar.md) — Aadhaar number with Verhoeff checksum
- [`validate_voter_id`](docs/tools/voter_id.md) — Voter ID (EPIC) format with legacy detection
- [`validate_driving_license`](docs/tools/driving_license.md) — DL format with state/RTO/year decode
- [`validate_passport`](docs/tools/passport.md) — Indian passport number format
- [`validate_cin`](docs/tools/cin.md) — Company Identification Number with full field decode
- [`validate_din`](docs/tools/din.md) — Director Identification Number format

### Tax Calculators (FY2025-26)
- [`calculate_income_tax`](docs/tools/income_tax.md) — Old vs new regime comparison with surcharge, rebate, cess
- [`calculate_tds`](docs/tools/tds.md) — TDS rate lookup and computation for 12+ sections
- [`calculate_gst`](docs/tools/gst_calculator.md) — GST breakdown (CGST/SGST/IGST/cess)
- [`calculate_surcharge`](docs/tools/surcharge.md) — Surcharge and marginal relief calculator

## Data Freshness

Datasets are bundled with the package for offline-first operation. An optional auto-update mechanism fetches the latest versions from jsDelivr CDN in the background.

- **Auto-update is non-blocking** — stale data triggers a background refresh; the current request uses existing data.
- **Opt out** — set `MCP_INDIA_STACK_NO_AUTO_UPDATE=1` environment variable to disable all update checks.
- **Manual refresh** — run `mcp-india-stack --refresh-all` to synchronously refresh all datasets from CDN.
- **Cache location** — platform-specific via `platformdirs` (e.g., `~/.cache/mcp-india-stack` on Linux).

## Bundled Data Size

This package bundles static datasets for offline-first workflows.

- IFSC dataset (Razorpay releases)
- India pincode dataset (GeoNames IN postal dump, CC-BY)
- HSN/SAC master (GST tutorial workbook transformed to CSV)
- State codes and curated UPI handles

Expected install footprint includes approximately 10-11MB compressed static data.

## Limitations

- GSTIN validation checks format and checksum, not active GSTN status.
- PAN validation is structural; PAN check character is not publicly algorithmic.
- HSN/SAC rates are static references and may vary by conditions/notifications.
- All tax calculations are estimates for FY2025-26. Actual liability may differ — consult a CA.
- Aadhaar, Voter ID, DL, Passport, CIN, DIN validators are format-only — they do not verify active status with issuing authorities.

## Legal and Attribution

See `NOTICES` for dataset attribution and licensing details.
