# Release Notes: MCP India Stack v0.8.0

**Release Date:** November 5, 2026  
**Tag:** `v0.8.0`  
**License:** MIT  
**Python Compatibility:** $\ge$ 3.10 (tested on Python 3.10, 3.11, 3.12, 3.13)

---

## Executive Summary

**MCP India Stack v0.8.0** introduces the **Authenticity System & Trust Architecture**, a milestone release transforming Indian identity and statutory data handling. 

Rather than relying on a simplistic boolean `valid: true/false`, every verifying tool now reports **how strongly** an entity or artifact is attested through a standardized multi-tier attestation envelope (`A0` to `A4`). 

The release preserves **zero-auth, pure offline-first defaults** while establishing cryptographic dataset provenance, offline digital signature verification for statutory documents, and an extensible, sandboxed live registry provider interface.

---

## 🛡️ The Authenticity System (`A0` – `A4`)

Every verifying tool now emits an additive `authenticity` envelope:

| Attestation Level | Meaning | Network Required | Primary Examples |
| :--- | :--- | :--- | :--- |
| **`A0`** | Structural syntax & checksum algorithm pass | No (Offline) | Mod-36 GSTIN checksum, Verhoeff Aadhaar checksum, Luhn mod-10 ISIN |
| **`A1`** | Cross-field consistency rules pass | No (Offline) | Embedded PAN in GSTIN, ROC jurisdiction in CIN, RTO prefix in DL |
| **`A2`** | Matched in bundled authoritative dataset | No (Offline) | RBI IFSC master directory, India Post pincode list, NSDL/CDSL ISIN list |
| **`A3`** | Cryptographic digital signature on artifact verified | No (Offline) | NIC signed B2B e-invoice QR code, UIDAI Paperless Offline e-KYC |
| **`A4`** | Confirmed by opt-in live registry provider | Yes (Opt-in) | Sandboxed API provider adapter (strictly opt-in via `verify_online=True`) |

### Six Core Semantic Invariants (Rules R1 – R6)
* **Rule R1 (Strict Monotonicity)**: The assigned level equals the highest consecutive tier whose checks all passed. Levels are never inflated.
* **Rule R2 (Invalidity Floor)**: When `valid=false`, `level` is `null`, and failed checks are enumerated.
* **Rule R3 (Dataset Miss Isolation)**: A dataset miss (`A2`) is never treated as forgery. The level stays at `A1`/`A0` with `not_found_in_dataset@<version>` in limitations.
* **Rule R4 (Anti-Enumeration Digest Safety)**: Never emits hashes or digests of low-entropy identifiers (Aadhaar, PAN, Mobile, UPI VPA). Only normalized public dataset records are digested.
* **Rule R5 (Deterministic Outputs)**: Identical inputs produce identical envelope representations; only `as_of` reflects the clock.
* **Rule R6 (PII Redaction)**: Full masking and redaction apply across all envelope limitation and detail strings.

---

## 📦 What's New by Component

### 1. In-Memory Validation & Cross-Field Consistency (PR 8a)
* **Standard Envelope**: Emitted across all 23 verifying and attesting tools (`level`, `checks`, `source`, `as_of`, `evidence_hash`, `limitations`, `registry_status`).
* **Cross-Field Rules**: Derived from official gazettes and statutory decoders:
  * `validate_gstin`: Checks embedded PAN against state code, entity index character, 14th character `'Z'` rule, and optional `expected_entity_type`.
  * `validate_cin`: Checks listing flag (`L`/`U`), ROC jurisdiction, company type (`PLC`, `PTC`, etc.), incorporation year bounds (`[1850, current_year]`), and sequential number.
  * `validate_driving_license`, `validate_fssai`, `validate_epf_code`, `validate_esic_code`: Validates state/RTO prefixes and plausible registration year.
* **Bulk Tool Summaries**: `bulk_validate_gstin`, `bulk_validate_pan`, and `bulk_validate_ifsc` include item-level authenticity plus top-level `authenticity_summary` counts by tier (`A0`–`A4`, `null`).

### 2. Cryptographic Dataset Manifests & Supply Chain Security (PR 8b)
* **Detached Ed25519 Signatures**: Every bundled and refreshed dataset (`ifsc`, `pincode`, `hsn`) ships with a signed JSON manifest containing monotonic versions, SHA-256 digests, byte sizes, and timestamps.
* **Verifying Key Ring**: Embedded key store (`keys/keys.json`) with key rotation metadata and revocation list (`keys/revocations.json`).
* **Anti-Rollback Protection**: Rejects any refreshed dataset payload with a version integer lower than or equal to current installed data.
* **CLI Verification**: New terminal verification tool:
  ```bash
  mcp-india-stack --verify-data
  ```
* **Strict Policy Mode**: Setting `MCP_INDIA_STACK_REQUIRE_SIGNED_DATA=1` enforces fail-closed startup if signatures or checksums fail.

### 3. Cryptographic Signed-Artifact Verification (PR 8c)
* **`verify_einvoice_qr`**: Verifies NIC RSA-signed JWTs extracted from B2B e-invoices against bundled trust anchors. Validates claims, verifies GSTINs, and cryptographically asserts the 64-character Invoice Reference Number (IRN) matching $\text{SHA-256}(\text{SellerGSTIN} + \text{DocTyp} + \text{DocNo} + \text{FinYr})$.
* **`verify_aadhaar_offline_artifact`**: Verifies UIDAI RSA digital signatures on Paperless Offline e-KYC XML artifacts. Supports password-protected ZIP files with 4-character share codes.
* **DPDP Act Compliance**: Masks Aadhaar numbers to the last 4 digits (`XXXXXXXX1234`) and extracts only non-sensitive demographic attributes; raw identifiers are never returned.
* **Defensive XML Processing**: Hardened against Billion Laughs XML bombs, Quadratic Blowup attacks, and external entity injection (XXE).
* **Optional Extra**: Lightweight base installation with optional cryptographic verification:
  ```bash
  pip install "mcp-india-stack[verify]"
  ```

### 4. Opt-in Registry Provider Interface (PR 8d)
* **Pluggable Architecture**: `BaseRegistryProvider(ABC)` interface with automatic discovery via Python entry points (`mcp_india_stack.providers`) and `MCP_INDIA_STACK_PROVIDERS`.
* **Zero-Network Default**: Verifying tools accept optional `verify_online: bool = False`. When false, zero network requests or provider executions occur.
* **`FixtureProvider`**: Shipped reference provider reading local JSON fixtures from disk for air-gapped demo, test, and staging environments (`MCP_INDIA_STACK_FIXTURE_DIR`).
* **Production Resilience**:
  * **SSRF Defense**: `validate_provider_url` blocks loopback (`127.0.0.1`, `localhost`), link-local (`169.254.169.254`), private RFC 1918 (`10.x`, `172.16.x`, `192.168.x`), and multicast destinations.
  * **3-State Circuit Breaker**: Trips to `OPEN` on 5 consecutive failures, fast-fails during a 60-second cooldown, and probes in `HALF_OPEN`.
  * **Token-Bucket Rate Limiter**: Rate-limits requests per provider to protect upstream quotas.
  * **Connect & Read Timeouts**: Enforces connect ($\le 3$s) and read ($\le 10$s) timeouts.

---

## 🔄 Backward Compatibility & Migration

* **Zero Breaking Changes**: All pre-existing response fields (`valid`, `data`, `errors`, `warnings`, `source`, `tool_version`) remain bit-for-bit identical.
* **Additive Only**: The `authenticity` object is purely additive.
* **Lightweight**: In-memory attestation adds $< 1.0\text{ ms}$ p95 overhead.

---

## 📊 Quality & Verification Metrics

* **Test Suite**: **1,238 automated tests** passing with **86.42% code coverage** (exceeds 80% threshold).
* **SAST Security Scan**: 0 Bandit issues identified.
* **Dependency Audit**: 0 `pip-audit` vulnerabilities.
* **Distribution Wheel Smoke Test**: Verified clean build and wheel execution in an isolated virtual environment.
