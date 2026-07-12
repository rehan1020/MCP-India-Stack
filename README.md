# 🇮🇳 MCP India Stack
> A high-performance, offline-first Model Context Protocol (MCP) server equipping AI agents with Indian financial, tax, and government APIs. Zero authentication required.

[![PyPI version](https://img.shields.io/pypi/v/mcp-india-stack.svg)](https://pypi.org/project/mcp-india-stack/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue.svg)](https://modelcontextprotocol.io)
[![CI](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/rehan1020/MCP-India-Stack/actions/workflows/ci.yml)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/137943ec-5cee-4de7-a22d-e55a7ac699bd)
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/rehan1020-mcp-india-stack-badge.png)](https://mseep.ai/app/rehan1020-mcp-india-stack)

## 📑 Table of Contents

- [Problem Statement](#problem-statement)
- [Tech Stack](#tech-stack)
- [Architecture Diagram](#architecture-diagram)
- [Team](#team)
- [Hackathon Track](#hackathon-track)
- [Demo & Links](#demo--links)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Tool Catalog](#tool-catalog)
- [Agent Workflows & Resources](#agent-workflows--resources)
- [Data Architecture & Freshness](#data-architecture--freshness)
- [Limitations](#limitations)
- [Legal & Attribution](#legal--attribution)
- [Launch Notes](#launch-notes)

---

## 📌 Problem Statement

- **Fragmented Access:** Indian fintech, identity, and tax APIs are heavily siloed, requiring multiple disjointed integrations.
- **High Barriers to Entry:** Existing solutions are plagued by paid subscriptions, strict rate limits, and complex API key management.
- **No Native AI Integration:** There is no MCP-native standard designed specifically for autonomous AI agents to validate GSTIN, PAN, IFSC, or compute tax data.
- **Latency & Reliability Issues:** Depending on remote third-party APIs for static/slow-moving datasets introduces unnecessary network delays and potential points of failure for AI workflows.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Protocol** | MCP (FastMCP) |
| **Runtime** | Python |
| **Distribution** | PyPI / Smithery |
| **Hosting** | Render |
| **Datasets** | Offline-bundled (jsDelivr CDN sync) |

---

## 🏗️ Architecture Diagram

![Architecture](./assets/architecture.png)
*MCP Client ↔ MCP Server ↔ 58 offline-first tool modules*

---

## 🧠 Team

**Team Name:** Solo Wizard

| Name | NAMESPACE Username | Role |
|---|---|---|
| Rehan Shashi | Rehan Shashi | Developer |

---

## 🏆 Hackathon Track

**Track:** Work, Finance & Digital Economy

---

## 🔗 Demo & Links

- **Demo Video:** [https://youtu.be/KAy6043Co0w?si=FIFfVRM2y3Zwv8oK](https://youtu.be/KAy6043Co0w?si=FIFfVRM2y3Zwv8oK)
- **Deployment:** [https://mseep.ai/app/rehan1020-mcp-india-stack](https://mseep.ai/app/rehan1020-mcp-india-stack)
- **PPT:** [https://gamma.app/docs/Problem-India-lacks-native-fintech-primitives-for-AI-agents-d1izzfemlvfvkf0?mode=doc](https://gamma.app/docs/Problem-India-lacks-native-fintech-primitives-for-AI-agents-d1izzfemlvfvkf0?mode=doc)
- **GitHub:** [https://github.com/rehan1020/MCP-India-Stack](https://github.com/rehan1020/MCP-India-Stack)
- **PyPI:** [https://pypi.org/project/mcp-india-stack/](https://pypi.org/project/mcp-india-stack/)

## ✨ Key Features

- **Offline-First Architecture**: Bundles compressed datasets for zero-latency lookups (IFSC, Pincodes, HSN/SAC). No API rate limits.
- **Zero Authentication**: No API keys, secrets, or subscriptions required. All logic runs locally.
- **Background Auto-Updates**: Non-blocking CDN fetching ensures your datasets never go stale without impacting request latency.
- **Comprehensive Coverage**: 58 dedicated tools for identity validation (PAN, Aadhaar, GSTIN, TAN, PRAN), tax calculation (Income Tax, TDS, GST), savings calculators (EPF, PPF, SIP), and master data lookups.
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
- [`lookup_ifsc`](docs/lookup_and_validation.md) — Bank branch details from IFSC code
- [`lookup_pincode`](docs/lookup_and_validation.md) — India pincode details and post offices
- [`lookup_hsn_code`](docs/lookup_and_validation.md) — HSN/SAC code lookup by code or keyword
- [`decode_state_code`](docs/lookup_and_validation.md) — GST state code metadata
- [`lookup_bbps_biller`](docs/lookup_and_validation.md) — BBPS biller directory lookup
- [`lookup_bank`](docs/lookup_and_validation.md) — Basic bank master lookup by name or code

### ✅ Validation Tools
- [`validate_gstin`](docs/lookup_and_validation.md) — GSTIN structure and checksum
- [`validate_pan`](docs/lookup_and_validation.md) — PAN format and entity type decode
- [`validate_upi_vpa`](docs/lookup_and_validation.md) — UPI VPA structure and provider decode
- [`validate_aadhaar`](docs/lookup_and_validation.md) — Aadhaar number with Verhoeff checksum (masked output)
- [`validate_voter_id`](docs/lookup_and_validation.md) — Voter ID (EPIC) format with legacy detection
- [`validate_driving_license`](docs/lookup_and_validation.md) — DL format with state/RTO/year decode
- [`validate_passport`](docs/lookup_and_validation.md) — Indian passport number format
- [`validate_cin`](docs/lookup_and_validation.md) — Company Identification Number with full field decode
- [`validate_din`](docs/lookup_and_validation.md) — Director Identification Number format
- [`validate_fssai`](docs/lookup_and_validation.md) — FSSAI license number validation and decode
- [`validate_epf_code`](docs/lookup_and_validation.md) — EPF establishment code validator
- [`validate_esic_code`](docs/lookup_and_validation.md) — ESIC employer code validator
- [`validate_tan`](docs/lookup_and_validation.md) — TAN validator
- [`validate_pran`](docs/lookup_and_validation.md) — PRAN validator for NPS
- [`validate_llpin`](docs/lookup_and_validation.md) — LLPIN validator
- [`decode_isin`](docs/lookup_and_validation.md) — ISIN decoder with Luhn validation
- [`decode_digilocker_uri`](docs/lookup_and_validation.md) — DigiLocker URI decoder and validator mapper
- [`decode_pan_type`](docs/lookup_and_validation.md) — Decode PAN entity type from the 4th character

### 📱 Identity & Contact
- [`validate_mobile_number`](docs/lookup_and_validation.md) — Mobile number with operator/circle detection

### ⚡ Bulk Operations
- [`bulk_validate_gstin`](docs/lookup_and_validation.md) — Parallel GSTIN batch validation
- [`bulk_validate_pan`](docs/lookup_and_validation.md) — Parallel PAN batch validation
- [`bulk_validate_ifsc`](docs/lookup_and_validation.md) — Parallel IFSC batch validation
- [`bulk_validate_aadhaar`](docs/lookup_and_validation.md) — Parallel Aadhaar batch validation

### 🧮 Tax & Financial Calculators (FY2025-26)
- [`calculate_income_tax`](docs/tax_and_finance.md) — Old vs new regime comparison with surcharge, rebate, cess
- [`calculate_tds`](docs/tax_and_finance.md) — TDS rate lookup and computation for 15+ sections
- [`calculate_gst`](docs/tax_and_finance.md) — GST breakdown (CGST/SGST/IGST/cess) with HSN lookup
- [`calculate_surcharge`](docs/tax_and_finance.md) — Surcharge and marginal relief calculator
- [`calculate_hra_exemption`](docs/tax_and_finance.md) — HRA exemption calculator for salary planning
- [`calculate_capital_gains`](docs/tax_and_finance.md) — Capital gains with Section 54/54F exemption
- [`calculate_advance_tax`](docs/tax_and_finance.md) — Advance tax estimator
- [`calculate_gst_late_fee`](docs/tax_and_finance.md) — GST late filing penalty
- [`calculate_income_tax_interest`](docs/tax_and_finance.md) — Sections 234A/B/C interest
- [`calculate_presumptive_tax`](docs/tax_and_finance.md) — 44AD/44ADA presumptive tax
- [`get_regulatory_deadlines`](docs/tax_and_finance.md) — Tax & regulatory compliance calendar


### 💰 Savings & Investment Calculators
- [`calculate_epf_esic`](docs/savings_and_investments.md) — EPF/ESIC contribution calculator
- [`calculate_emi`](docs/savings_and_investments.md) — Loan EMI with amortization schedule
- [`calculate_gratuity`](docs/savings_and_investments.md) — Gratuity under Payment of Gratuity Act
- [`calculate_ppf_maturity`](docs/savings_and_investments.md) — PPF maturity projections
- [`calculate_fd_maturity`](docs/savings_and_investments.md) — Fixed Deposit maturity
- [`calculate_rd_maturity`](docs/savings_and_investments.md) — Recurring Deposit maturity
- [`calculate_sip_returns`](docs/savings_and_investments.md) — SIP returns with inflation adjustment
- [`calculate_step_up_sip`](docs/savings_and_investments.md) — Step-up SIP comparison
- [`calculate_nps_projection`](docs/savings_and_investments.md) — NPS corpus and pension
- [`calculate_sukanya_samriddhi`](docs/savings_and_investments.md) — SSY and SCSS calculator

### 🏠 Real Estate
- [`calculate_home_vs_rent`](docs/savings_and_investments.md) — Buy vs rent financial comparison
- [`calculate_leave_encashment_tax`](docs/savings_and_investments.md) — Section 10(10AA) leave encashment

### 💼 HR & Payroll
- [`calculate_professional_tax`](docs/tax_and_finance.md) — State-wise professional tax
- [`calculate_salary_restructuring`](docs/tax_and_finance.md) — Tax-optimized salary restructuring

### 🏦 Banking & Payments
- [`calculate_neft_rtgs_imps_charges`](docs/banking_and_aa.md) — Transaction charges

### 🔐 Account Aggregator (Offline)
- [`build_aa_consent_request`](docs/banking_and_aa.md) — AA consent request builder
- [`validate_aa_consent_artifact`](docs/banking_and_aa.md) — AA consent validator
- [`decode_aa_fi_type`](docs/banking_and_aa.md) — AA FI type decoder

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
- `0.4.2` package metadata and changelog coverage.
- A complete MCP server-card under `docs/.well-known/mcp/server-card.json`.
- Local setup and publishing steps in [`SETUP.md`](SETUP.md).
- Contribution guidance and versioning policy in [`CONTRIBUTING.md`](CONTRIBUTING.md).

### Bug fixes in v0.4.2 (Round 2 — Deep Code Audit)
- **Capital Gains**: Asset-type-specific LTCG thresholds — real estate 24mo, gold/debentures 36mo, crypto always 30% flat.
- **EPF/ESIC**: Employee EPF correctly capped at ₹15K wage ceiling. Added `voluntary_pf_on_actual` for VPF.
- **HRA**: Removed Bangalore/Hyderabad/Pune from metro cities. Only Delhi/Mumbai/Chennai/Kolkata get 50%.
- **Presumptive Tax**: Full 7-slab new regime coverage with 87A rebate (was truncated at 3 slabs).
- **GST Late Fee**: GSTR9 cap enforced (0.25% of turnover). Nil return rate corrected to ₹20/day.
- **Income Tax Interest**: Section 234C uses cumulative paid vs required (not single-quarter).
- **Advance Tax**: Installments show incremental `installment_amount` (not confusing cumulative).
- **Salary Restructuring**: Removed obsolete ₹19,200 conveyance exemption. Standard deduction (₹75K) shown.

### Bug fixes in v0.4.1
- **Security**: Masked Aadhaar number leakage in response fields.
- **Validation**: Fixed mobile number over-counting digits issue.
- **Tax Rules**: Corrected Presumptive Tax (44AD/44ADA) thresholds to FY25-26 rules.
- **Financial**: Fixed Step-up SIP compounding return calculation.
- **Data**: Added missing HSN codes (8517, 9401, 2523, 3004, 8708) with correct GST rates.
- **Professional Tax**: Fixed annual total calculations based on correct monthly slabs.
- **Income Tax**: Fixed 80D deduction cap for senior citizens.
- **ISIN**: Fixed Luhn checksum multi-digit expansion logic.
- **EMI Calculator**: Improved error responses to not leak fallback fields on invalid inputs.
- **Advance Tax**: Added support for overriding internal computations with user-provided `tax_liability`.

---
**Offline-First Guarantee**: All tools in this package work without an internet connection. No API keys required. No data is sent to any external server. All datasets are bundled in the package at install time.
