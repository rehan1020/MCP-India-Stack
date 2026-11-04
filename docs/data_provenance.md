# Data Provenance & Dataset Registry

This document establishes the official data provenance registry for all bundled datasets included in `mcp-india-stack` under `src/mcp_india_stack/data/`.

Every dataset is audited for upstream statutory authority, licensing, retrieval mechanism, update cadence, verification status, and transformation tooling.

---

## 1. Master Dataset Provenance Table

| Dataset File | Upstream Authority | License | Retrieval Method | Refresh Cadence | Last Refreshed | Transform Script |
|---|---|---|---|---|---|---|
| `hsn/hsn_master.csv` | Central Board of Indirect Taxes and Customs (CBIC) & GSTN | NDSAP / Government Open Data | Direct export from GST Portal tutorial resources | Quarterly | 2026-03-21 | None (CSV direct) |
| `ifsc/IFSC.csv` | Reserve Bank of India (RBI) via Razorpay Open Source | MIT / Public Domain | Release asset download from GitHub releases | Monthly | 2026-03-21 | None (CSV direct) |
| `legal/bare_acts.json` | Legislative Department, Ministry of Law and Justice (India Code) | Public Domain (Sec 52(1)(q) Copyright Act) | Structured compilation from official India Code legislative database | Annual | 2026-10-29 | `scripts/build_legal_data.py` |
| `legal/court_establishments.json` | Supreme Court of India & e-Courts Mission Mode Project | Public Domain | Official e-Courts directory synthesis | Annual | 2026-10-29 | `scripts/build_legal_data.py` |
| `legal/court_fees.json` | State Legislative Assemblies via State Gazettes & India Code | Public Domain | Statutory fee schedule extraction from state enactment gazettes | Per statutory amendment | 2026-10-29 | `scripts/build_legal_data.py` |
| `legal/ipc_bns_crosswalk.json` | Ministry of Home Affairs, Government of India (Gazette of India) | Public Domain | Crosswalk extraction from Criminal Law Amendment Acts (45, 46, 47 of 2023) | Static / Per amendment | 2026-10-29 | `scripts/build_legal_data.py` |
| `legal/limitation_periods.json` | Legislative Department, Ministry of Law and Justice (India Code) | Public Domain | Codified schedule from Limitation Act, 1963 (Act 36 of 1963) | Static | 2026-10-29 | `scripts/build_legal_data.py` |
| `legal/stamp_duty.json` | State Revenue & Registration Departments / State Gazettes | Public Domain | Conveyance and deed duty schedules extracted from State Stamp Acts | Per statutory amendment | 2026-10-29 | `scripts/build_legal_data.py` |
| `pincode/pincode.csv.gz` | Department of Posts, Ministry of Communications & GeoNames | CC-BY 4.0 | GeoNames IN.zip cross-referenced with data.gov.in postal directory | Semiannual | 2026-03-21 | Gzip compression stream |
| `rti/rti_fees.json` | Department of Personnel and Training (DoPT) & State Information Commissions | Public Domain | RTI Rules 2012 and State RTI schedule compilation | Annual | 2026-10-29 | `scripts/build_legal_data.py` |
| `state_codes/state_codes.json` | Goods and Services Tax Council (GST Council) | Public Domain | Statutory 2-digit GST state codes codified from GST Rules | Static / Per new territory | 2026-03-21 | None (JSON direct) |
| `upi/upi_handles.json` | National Payments Corporation of India (NPCI) | Open Public Directory | Synthesis from NPCI UPI Live PSP Members registry | Quarterly | 2026-03-21 | None (JSON direct) |
| `dataset_checksums.json` | Internal Package Integrity Gate | Apache-2.0 | Automated SHA-256 generation over bundled data files | Every build / release | 2026-10-29 | `scripts/build_manifest.py` |

---

## 2. Dataset Specifics & Authority References

### 2.1 HSN / SAC Codes (`hsn/hsn_master.csv`)
- **Authority:** [Central Board of Indirect Taxes & Customs (CBIC)](https://www.cbic.gov.in/) & [GST Council](https://gstcouncil.gov.in/)
- **Description:** 4-digit and 6-digit Harmonized System of Nomenclature (HSN) and Services Accounting Codes (SAC) with standard GST slab rates (0%, 5%, 12%, 18%, 28%).
- **Verification:** Sourced from CBIC notifications and GSTN master tables.

### 2.2 Bank IFSC Codes (`ifsc/IFSC.csv`)
- **Authority:** [Reserve Bank of India (RBI)](https://www.rbi.org.in/) and [NPCI](https://www.npci.org.in/)
- **Description:** Complete listing of Indian Financial System Codes (IFSC), bank names, branches, and payment network capabilities (RTGS, NEFT, IMPS, UPI).
- **Verification:** Curated by Razorpay from daily RBI circulars.

### 2.3 Legal Reference Datasets (`legal/`)
- **Bare Acts:** Acts of Parliament hosted on [India Code](https://www.indiacode.nic.in/).
- **Criminal Laws Crosswalk:** Maps old criminal statutes (Indian Penal Code 1860, Code of Criminal Procedure 1973, Indian Evidence Act 1872) to the new Bharatiya Nagarik Suraksha Sanhita (BNSS 2023), Bharatiya Nyaya Sanhita (BNS 2023), and Bharatiya Sakshya Adhiniyam (BSA 2023). Flagged for 1-to-many migrations.
- **Court Fees & Stamp Duty:** State-specific ad-valorem and fixed fee schedules for supported states (Delhi, Maharashtra, Karnataka, Tamil Nadu). Unsupported states fail safely with `coverage: partial` and `unsupported_state` error code.
- **Limitation Deadlines:** Codified periods under Articles 1-137 of Limitation Act 1963, including Section 4 court holiday rollover and Section 12 exclusion calculations.

### 2.4 All-India PIN Codes (`pincode/pincode.csv.gz`)
- **Authority:** [Department of Posts](https://www.indiapost.gov.in/) & [GeoNames](https://www.geonames.org/)
- **Description:** 6-digit PIN codes mapping to delivery post offices, taluks, districts, and states. Compressed with gzip to conserve package size.

### 2.5 RTI Fee Schedules (`rti/rti_fees.json`)
- **Authority:** [Department of Personnel and Training (DoPT)](https://dopt.gov.in/)
- **Description:** Application fees, appeal fees, BPL exemption rules, and acceptable payment modes across Central and State public authorities.

### 2.6 GST State Codes (`state_codes/state_codes.json`)
- **Authority:** [Goods and Services Tax Council](https://gstcouncil.gov.in/)
- **Description:** Two-digit numerical codes representing states and union territories prefixed on all GSTINs.

### 2.7 UPI Handles (`upi/upi_handles.json`)
- **Authority:** [National Payments Corporation of India (NPCI)](https://www.npci.org.in/)
- **Description:** Directory of certified Virtual Payment Address (VPA) handles mapped to authorized third-party app providers (TPAPs) and sponsor banks.

### 2.8 Checksum Manifest (`dataset_checksums.json`)
- **Authority:** `mcp-india-stack` build pipeline
- **Description:** Cryptographic SHA-256 checksums of every bundled dataset to guarantee offline data integrity and prevent tampering.
