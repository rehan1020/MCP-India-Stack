# 🇮🇳 MCP India Stack

[![PyPI version](https://img.shields.io/pypi/v/mcp-india-stack.svg)](https://pypi.org/project/mcp-india-stack/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/137943ec-5cee-4de7-a22d-e55a7ac699bd)
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/rehan1020-mcp-india-stack-badge.png)](https://mseep.ai/app/rehan1020-mcp-india-stack)

> A high-performance, offline-first Model Context Protocol (MCP) server equipping AI agents with Indian financial, tax, and government APIs. Zero authentication required.

## ✨ Key Features

- **Offline-First Architecture**: Bundles compressed datasets for zero-latency lookups (IFSC, Pincodes, HSN/SAC). No API rate limits.
- **Zero Authentication**: No API keys, secrets, or subscriptions required. All logic runs locally.
- **Background Auto-Updates**: Non-blocking CDN fetching ensures your datasets never go stale without impacting request latency.
- **Comprehensive Coverage**: 30 dedicated tools for identity validation (PAN, Aadhaar, GSTIN), tax calculation (Income Tax, TDS, GST), and master data lookups.
- **Enterprise-Ready**: Thread-pool accelerated bulk validation tools for processing large batches of vendor or customer data.

---

## 🚀 Quick Start

### Installation

```bash
pip install mcp-india-stack
```

### Claude Desktop Configuration

Add the following to your `claude_desktop_config.json` file to enable the India Stack in Claude Desktop:

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "mcp-india-stack": {
      "command": "python",
      "args": ["-m", "mcp_india_stack"]
    }
  }
}
```

**macOS/Linux** (`~/Library/Application Support/Claude/claude_desktop_config.json` or `~/.config/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "mcp-india-stack": {
      "command": "python3",
      "args": ["-m", "mcp_india_stack"]
    }
  }
}
```

---

## 🛠️ Tool Catalog

### 🔍 Lookup Tools
- [`lookup_ifsc`](docs/tools/ifsc.md) — Bank branch details from IFSC code
- [`lookup_pincode`](docs/tools/pincode.md) — India pincode details and post offices
- [`lookup_hsn_code`](docs/tools/hsn.md) — HSN/SAC code lookup by code or keyword
- [`decode_state_code`](docs/tools/state_code.md) — GST state code metadata
- [`lookup_bbps_biller`](docs/tools/bbps.md) — BBPS biller directory lookup
- [`lookup_bank`](docs/tools/bank.md) — Basic bank master lookup by name or code

### ✅ Validation Tools
- [`validate_gstin`](docs/tools/gstin.md) — GSTIN structure and checksum
- [`validate_pan`](docs/tools/pan.md) — PAN format and entity type decode
- [`validate_upi_vpa`](docs/tools/upi.md) — UPI VPA structure and provider decode
- [`validate_aadhaar`](docs/tools/aadhaar.md) — Aadhaar number with Verhoeff checksum
- [`validate_voter_id`](docs/tools/voter_id.md) — Voter ID (EPIC) format with legacy detection
- [`validate_driving_license`](docs/tools/driving_license.md) — DL format with state/RTO/year decode
- [`validate_passport`](docs/tools/passport.md) — Indian passport number format
- [`validate_cin`](docs/tools/cin.md) — Company Identification Number with full field decode
- [`validate_din`](docs/tools/din.md) — Director Identification Number format
- [`validate_fssai`](docs/tools/fssai.md) — FSSAI license number validation and decode
- [`validate_epf_code`](docs/tools/epf.md) — EPF establishment code validator
- [`validate_esic_code`](docs/tools/esic.md) — ESIC employer code validator
- [`decode_digilocker_uri`](docs/tools/digilocker.md) — DigiLocker URI decoder and validator mapper
- [`decode_pan_type`](docs/tools/pan.md) — Decode PAN entity type from the 4th character

### ⚡ Bulk Operations
- [`bulk_validate_gstin`](docs/tools/gstin.md) — Parallel GSTIN batch validation
- [`bulk_validate_pan`](docs/tools/pan.md) — Parallel PAN batch validation
- [`bulk_validate_ifsc`](docs/tools/ifsc.md) — Parallel IFSC batch validation

### 🧮 Tax & Financial Calculators (FY2025-26)
- [`calculate_income_tax`](docs/tools/income_tax.md) — Old vs new regime comparison with surcharge, rebate, cess
- [`calculate_tds`](docs/tools/tds.md) — TDS rate lookup and computation for 12+ sections
- [`calculate_gst`](docs/tools/gst_calculator.md) — GST breakdown (CGST/SGST/IGST/cess)
- [`calculate_surcharge`](docs/tools/surcharge.md) — Surcharge and marginal relief calculator
- [`calculate_hra_exemption`](docs/tools/hra.md) — HRA exemption calculator for salary planning
- [`calculate_capital_gains`](docs/tools/capital_gains.md) — Capital gains tax helper
- [`calculate_advance_tax`](docs/tools/advance_tax.md) — Advance tax estimator

---

## 🔄 Agent Workflows & Resources

### Prompt Workflows ([Overview](docs/prompts.md))
Built-in prompt templates to guide AI agents through complex multi-step tasks:
- [`vendor_kyc`](docs/workflows/vendor_kyc.md) — GSTIN, PAN, and IFSC verification sequence.
- [`salary_planner`](docs/workflows/salary_planner.md) — Income, HRA, and optimized take-home salary planning.
- [`invoice_audit`](docs/workflows/invoice_audit.md) — Cross-referencing GSTINs, HSN codes, and applicable GST rates.

### Server Resources ([Overview](docs/resources.md))
Dynamic JSON resources provided directly to the LLM context:
- `india://status` — Version, DB connectivity, and runtime flags
- `india://changelog` — Structured changelog resource
- `india://schema/*` — JSON schemas for all tool outputs

---

## 📡 Data Architecture & Freshness

This package bundles static datasets for offline-first workflows (approx. 10-11MB compressed footprint), covering IFSCs, Pincodes, HSN/SAC masters, and curated UPI handles.

An optional auto-update mechanism fetches the latest versions from the jsDelivr CDN in the background:
- **Non-blocking**: Stale data triggers a background refresh; the current request immediately uses existing cached data to ensure zero latency.
- **Opt out**: Set the `MCP_INDIA_STACK_NO_AUTO_UPDATE=1` environment variable to disable all update checks.
- **Manual refresh**: Run `mcp-india-stack --refresh-all` to synchronously refresh all datasets from the CDN.
- **Cache location**: Platform-specific via `platformdirs` (e.g., `~/.cache/mcp-india-stack` on Linux).

---

## ⚠️ Limitations

- **Stateless Validation**: GSTIN, Aadhaar, Voter ID, DL, Passport, CIN, and DIN validators check structural formatting and checksums only. They **do not** verify active registration status with government issuing authorities.
- **Algorithmic Constraints**: PAN validation is structural; the PAN check character logic is not publicly verifiable.
- **Tax Estimates**: All tax calculations are algorithmic estimates based on FY2025-26 rules. Actual liability may differ. Always consult a Chartered Accountant.
- **Static Rates**: HSN/SAC rates are static references and may vary based on specific conditions or new government notifications.

---

## ⚖️ Legal & Attribution

See [`NOTICES`](NOTICES) for detailed dataset attribution, licensing details, and third-party acknowledgments.

---

## 🚀 Launch Notes

This repository is release-ready for GitHub launch with:
- `0.3.0` package metadata and changelog coverage.
- A complete MCP server-card under `docs/.well-known/mcp/server-card.json`.
- Local setup and publishing steps in [`SETUP.md`](SETUP.md).
- Contribution guidance and versioning policy in [`CONTRIBUTING.md`](CONTRIBUTING.md).
