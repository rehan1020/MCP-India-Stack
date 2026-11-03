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
*MCP Client ↔ MCP Server ↔ 78 offline-first tool modules*

---

## 🔗 Links

- **Deployment:** [https://pypi.org/project/mcp-india-stack/](https://pypi.org/project/mcp-india-stack/)
- **PPT:** [https://gamma.app/docs/Problem-India-lacks-native-fintech-primitives-for-AI-agents-d1izzfemlvfvkf0?mode=doc](https://gamma.app/docs/Problem-India-lacks-native-fintech-primitives-for-AI-agents-d1izzfemlvfvkf0?mode=doc)
- **GitHub:** [https://github.com/rehan1020/MCP-India-Stack](https://github.com/rehan1020/MCP-India-Stack)
- **PyPI:** [https://pypi.org/project/mcp-india-stack/](https://pypi.org/project/mcp-india-stack/)

## ✨ Key Features

- **Offline-First Architecture**: Bundles compressed datasets for zero-latency lookups (IFSC, Pincodes, HSN/SAC). No API rate limits.
- **Zero Authentication**: No API keys, secrets, or subscriptions required. All logic runs locally.
- **Background Auto-Updates**: Non-blocking CDN fetching ensures your datasets never go stale without impacting request latency.
- **Comprehensive Coverage**: 78 dedicated tools for identity validation (PAN, Aadhaar, GSTIN, TAN, PRAN), tax calculation (Income Tax, TDS, GST), savings calculators (EPF, PPF, SIP), and master data lookups.
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

### 📈 Stock Market
- `get_stock_quote` — Fetch live/delayed Indian stock quotes and summaries (NSE/BSE) using yfinance.
- `get_stock_history` — Fetch historical end-of-day data for Indian stocks using yfinance.

### ⚖️ Legal Reference
- [`decode_cnr_number`](docs/legal_reference.md) — CNR (Case Number Record) decoder and validator
- [`lookup_court_establishment_code`](docs/legal_reference.md) — Court establishment code directory lookup
- [`lookup_ipc_section`](docs/legal_reference.md) — IPC section lookup with BNS crosswalk
- [`lookup_bns_section`](docs/legal_reference.md) — BNS section lookup with IPC crosswalk
- [`lookup_crpc_section`](docs/legal_reference.md) — CrPC section lookup with BNSS crosswalk
- [`lookup_bnss_section`](docs/legal_reference.md) — BNSS section lookup with CrPC crosswalk
- [`lookup_evidence_act_section`](docs/legal_reference.md) — Indian Evidence Act section lookup
- [`lookup_bsa_section`](docs/legal_reference.md) — BSA section lookup with IEA crosswalk
- [`decode_ipc_bns_crosswalk`](docs/legal_reference.md) — Bidirectional IPC↔BNS section crosswalk
- [`calculate_limitation_deadline`](docs/legal_reference.md) — Limitation Act 1963 deadline calculator
- [`calculate_court_fee`](docs/legal_reference.md) — State-wise court fee calculator
- [`calculate_stamp_duty`](docs/legal_reference.md) — State-wise stamp duty and registration fee calculator

### 📋 RTI Toolkit
- [`calculate_rti_fee`](docs/rti_toolkit.md) — RTI application fee calculator (central + state)
- [`calculate_rti_deadline`](docs/rti_toolkit.md) — RTI response and appeal deadline calculator
- [`calculate_rti_penalty_estimate`](docs/rti_toolkit.md) — RTI penalty estimator (Section 20)
- [`draft_rti_application`](docs/rti_toolkit.md) — RTI application drafter (Section 6)
- [`draft_first_appeal`](docs/rti_toolkit.md) — First appeal template generator (Section 19)
- [`draft_second_appeal`](docs/rti_toolkit.md) — Second appeal template generator (Section 19)

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

All datasets are bundled directly within the package and checksum-verified at build time:
- **Offline First**: Zero runtime network calls for dataset queries. No external CDN dependency or cache shadowing.
- **Deterministic**: Data freshness is tied to package releases. To receive updated datasets, upgrade `mcp-india-stack`.
- **Integrity**: Bundled dataset integrity is verified against a build-time SHA-256 manifest.

---

## ⚠️ Limitations

- **Stateless Validation**: GSTIN, Aadhaar, Voter ID, DL, Passport, CIN, and DIN validators check structural formatting and checksums only. They **do not** verify active registration status with government issuing authorities.
- **Algorithmic Constraints**: PAN validation is structural; the PAN check character logic is not publicly verifiable.
- **Tax Estimates**: All tax calculations are algorithmic estimates based on FY2025-26 rules. Actual liability may differ. Always consult a Chartered Accountant.
- **Static Rates**: HSN/SAC rates are static references and may vary based on specific conditions or new government notifications.

---

## ⚖️ Legal & Attribution

See [`NOTICES`](NOTICES) for detailed dataset attribution, licensing details, and third-party acknowledgments.

See [`LEGAL_NOTICE.md`](LEGAL_NOTICE.md) for important legal disclaimers including:
- **No Government Affiliation** — This project is not affiliated with NIC, eCourts, MeitY, or any government body.
- **Not Legal Advice** — All outputs (bare-act lookups, limitation calculations, court fee estimates, stamp duty estimates, RTI deadline/penalty calculations) are algorithmic estimates, not legal advice.
- **Data Accuracy** — State-subject data (court fees, stamp duty) carries `as_of` / `last_verified` fields and is not live-verified against issuing authorities.
- **Personal Data** — Identity validation (Aadhaar, PAN, etc.) is structural/checksum only. Users are responsible for DPDP Act compliance.

---



## 🚀 Launch Notes

This repository is release-ready for GitHub launch with:
- `0.7.0` package metadata and changelog coverage.
- A complete MCP server-card under `docs/.well-known/mcp/server-card.json`.
- Local setup and publishing steps in [`SETUP.md`](SETUP.md).
- Contribution guidance and versioning policy in [`CONTRIBUTING.md`](CONTRIBUTING.md).

### What's New in v0.7.0 — Security Hardening, Full Parity & Offline Invariants
- **Offline Architecture & Tool Network Tiers**: Canonical network classification (none/optional/required) across all 78 tools.
- **Hardened Supply Chain**: CDN refresh pipeline with strict HTTPS, host allowlists, size/decompression bomb caps, monotonic version checks, and atomic staging.
- **100% Modular Tool Parity**: Full core module extraction and parity across all 78 registered tools.
- **Architectural Regression Guards**: G01-G20 invariants enforcing zero unhandled exceptions, constant-time auth, and fail-closed network safeguards.

### Previous Releases
- **v0.6.0**: Legal Reference (CNR decoder, court establishment lookup, bare-act section lookups for IPC/BNS/CrPC/BNSS/IEA/BSA, IPC↔BNS crosswalk, limitation period calculator, court fee, stamp duty) and RTI Toolkit (fee calculator, deadline tracker, penalty estimator, templates). Added yfinance-based market data tools.
- **v0.4.x**: Deep statutory audit across capital gains thresholds, EPF wage ceilings, metro HRA rules, 7-slab presumptive tax, and GST late fee caps. See [CHANGELOG.md](CHANGELOG.md) for detailed history.

---

### Offline-First Guarantee

The package classifies every tool under an authoritative network access attribute (`none`, `optional`, or `required`), surfaced programmatically in the `india://status` MCP resource (`tools_network`):

| Network Tier | Policy | Tool Count | Tools Included |
|---|---|---|---|
| `none` (Network: None) | Pure offline execution. Zero network calls, zero external endpoints, no sockets opened. Computations, format checks, checksum algorithms, and tax rules execute entirely in-process using local logic. | 71 | `validate_gstin`, `bulk_validate_gstin`, `validate_pan`, `bulk_validate_pan`, `decode_pan_type`, `validate_upi_vpa`, `decode_state_code`, `validate_aadhaar`, `bulk_validate_aadhaar`, `validate_voter_id`, `validate_driving_license`, `validate_passport`, `validate_cin`, `validate_din`, `validate_fssai`, `validate_tan`, `validate_mobile_number`, `validate_pran`, `validate_llpin`, `decode_isin`, `lookup_bank`, `lookup_bbps_biller`, `validate_epf_code`, `validate_esic_code`, `decode_digilocker_uri`, `build_aa_consent_request`, `validate_aa_consent_artifact`, `decode_aa_fi_type`, `calculate_income_tax`, `calculate_tds`, `calculate_surcharge`, `calculate_hra_exemption`, `calculate_capital_gains`, `calculate_advance_tax`, `calculate_epf_esic`, `calculate_emi`, `calculate_gratuity`, `calculate_ppf_maturity`, `calculate_fd_maturity`, `calculate_rd_maturity`, `calculate_sip_returns`, `calculate_step_up_sip`, `calculate_nps_projection`, `calculate_sukanya_samriddhi`, `calculate_home_vs_rent`, `calculate_gst_late_fee`, `calculate_income_tax_interest`, `calculate_presumptive_tax`, `calculate_professional_tax`, `calculate_leave_encashment_tax`, `calculate_salary_restructuring`, `calculate_neft_rtgs_imps_charges`, `get_regulatory_deadlines`, `decode_cnr_number`, `lookup_court_establishment_code`, `lookup_ipc_section`, `lookup_bns_section`, `lookup_crpc_section`, `lookup_bnss_section`, `lookup_evidence_act_section`, `lookup_bsa_section`, `decode_ipc_bns_crosswalk`, `calculate_limitation_deadline`, `calculate_court_fee`, `calculate_stamp_duty`, `calculate_rti_fee`, `calculate_rti_deadline`, `calculate_rti_penalty_estimate`, `draft_rti_application`, `draft_first_appeal`, `draft_second_appeal` |
| `optional` (Network: Optional) | Datasets are bundled locally offline (IFSC master, postal pincodes, HSN/SAC master). When enabled, background non-blocking CDN refresh or optional live lookup enriches local data. If network is unavailable or blocked, falls back seamlessly to bundled local datasets without blocking or error. | 5 | `lookup_ifsc`, `bulk_validate_ifsc`, `lookup_pincode`, `lookup_hsn_code`, `calculate_gst` |
| `required` (Network: Required) | Live financial market data feeds. Must reach market upstream endpoints (e.g. Yahoo Finance) to retrieve current quotes or historical prices. If network is blocked or unavailable, returns structured error envelopes without unhandled exceptions. | 2 | `get_stock_quote`, `get_stock_history` |
