# Authenticity System

The **MCP India Stack Authenticity System** provides explicit, multi-tier attestation levels (`A0` to `A4`) for all verifying tools. Instead of returning only a binary `valid: true/false` flag, each verifying tool states **how strongly** an identifier or record is attested, its provenance, verified checks, and remaining limitations.

---

## 1. Attestation Levels

| Level | Attestation Meaning | Network Required | Primary Example |
| :--- | :--- | :--- | :--- |
| **A0** | Format syntax and checksum algorithm pass | No (Offline) | Mod-36 GSTIN checksum, Verhoeff Aadhaar checksum, Luhn mod-10 ISIN checksum |
| **A1** | All applicable cross-field consistency rules pass | No (Offline) | Embedded PAN in GSTIN, ROC jurisdiction in CIN, RTO in DL, FSSAI year & type |
| **A2** | Record present in a bundled authoritative dataset | No (Offline) | RBI IFSC master directory, India Post pincode list, NSDL/CDSL ISIN registry |
| **A3** | Cryptographic digital signature on supplied artifact verified | No (Offline) | NIC signed e-invoice QR code, UIDAI secure offline XML/QR artifact |
| **A4** | Confirmed by an opt-in authoritative live registry provider | Yes (Opt-in) | Sandboxed API provider adapter (strictly opt-in via environment configuration) |

---

## 2. Standard Authenticity Envelope

Every verifying tool includes an additive `authenticity` object in its response:

```json
{
  "authenticity": {
    "level": "A1",
    "checks": [
      {
        "name": "gstin_format_syntax",
        "passed": true,
        "level": "A0",
        "detail": "15-character uppercase alphanumeric structure"
      },
      {
        "name": "gstin_mod36_checksum",
        "passed": true,
        "level": "A0",
        "detail": "Luhn mod-36 checksum character verification"
      },
      {
        "name": "embedded_pan_consistency",
        "passed": true,
        "level": "A1",
        "detail": "Characters 3-12 form a structurally valid Indian PAN"
      },
      {
        "name": "state_code_consistency",
        "passed": true,
        "level": "A1",
        "detail": "Leading 2 digits correspond to an assigned state/UT code"
      }
    ],
    "source": "GST Council / CBIC",
    "dataset_version": null,
    "as_of": "2026-11-05",
    "evidence_hash": null,
    "limitations": [
      "active registration status not verified",
      "taxpayer filing compliance not verified"
    ]
  }
}
```

For batch validation tools (`bulk_validate_*`), each item in `results` contains its own `authenticity` envelope, and the top-level response envelope provides an aggregated summary:

```json
{
  "authenticity": {
    "summary": {
      "A0": 0,
      "A1": 42,
      "A2": 5,
      "A3": 0,
      "A4": 0,
      "null": 3
    }
  }
}
```

---

## 3. Core Evaluation Rules (R1–R6)

The Authenticity System guarantees the following invariant rules:

* **R1 (No Inflation)**: The reported `level` equals the highest consecutive level whose checks all passed. If an `A0` check passes but an `A1` check fails, the level remains `A0` even if downstream checks succeed.
* **R2 (Null on Invalid)**: When `valid=false`, `level=null`. All failed checks are explicitly listed in `checks[]`.
* **R3 (Dataset Miss ≠ Forgery)**: Authoritative datasets lag reality. A lookup miss in a bundled dataset (e.g., a newly opened bank branch or new pincode) is **not** evidence of fraud or forgery. The tool stays at `A1` or `A0` and attaches the limitation `not_found_in_dataset@<version>`.
* **R4 (Prohibition of Low-Entropy Identifier Hashes)**: To protect personal privacy under DPDP Act 2023, the system never emits a hash or digest of low-entropy identifiers (Aadhaar, PAN, mobile number, UPI VPA) in `evidence_hash` or elsewhere, because SHA-256 digests over small numeric/alphanumeric domains are easily reversed via enumeration or rainbow tables. `evidence_hash` is computed only over normalized public dataset records (e.g., bank branch addresses, post offices).
* **R5 (Deterministic Output)**: Output is strictly deterministic. Only `as_of` may reflect the evaluation date.
* **R6 (DPDP Compliance & Redaction)**: Aadhaar numbers and sensitive PII are masked in check descriptions and limitations.

---

## 4. How NOT to Misread "Valid"

> [!WARNING]
> A response of `valid: true` at level `A0` or `A1` proves only that an identifier satisfies mathematical format and structural cross-field consistency rules.

It does **not** prove:
1. That the taxpayer, company, or individual is actively registered with the respective government authority.
2. That the entity has not been suspended, struck off, or canceled.
3. That the bearer of the identifier is the legitimate owner.

Always review `authenticity.limitations` for the exact operational boundaries of the verification.

---

## 5. What A2 Authoritative Matching Does and Does Not Prove

* **What A2 Proves**: The identifier was verified against a bundled snapshot of an authoritative master record (e.g., RBI's official IFSC list, Department of Posts pincode directory, or SEBI ISIN schedule).
* **What A2 Does Not Prove**: It does not prove real-time operational status (such as an unannounced bank branch closure, recent bank merger, or temporary service outage).

---

## 6. Performance Guarantees

The evaluation of A0–A2 rules is entirely zero-auth and executed in-memory:
* **Per-call overhead**: Adds under 1.0 ms p95 latency relative to raw validation.
* **Bulk validation**: Batch operations of up to 500 items execute within bounded CPU limits without external network latency.

---

## 7. Signed Dataset Manifests & Supply Chain Security

To protect offline-first datasets against tampering, rollbacks, and supply chain corruption:

1. **Cryptographic Manifests**: Every bundled and refreshed dataset includes a signed JSON manifest containing:
   * `name`: Dataset identifier (`ifsc`, `pincode`, `hsn`)
   * `version`: Monotonically increasing version integer (anti-rollback)
   * `sha256`: Cryptographic SHA-256 hash of the dataset bytes
   * `size`: Exact byte length
   * `source`: Upstream authoritative origin
   * `generated_at` & `expires_at`: Validity window timestamps
   * `key_id`: ID of the signing key
   * `signature`: Detached Ed25519 signature over canonical manifest JSON
2. **Bundled Verifying Keys & Revocation**:
   * Keys ship in `src/mcp_india_stack/keys/keys.json` with validity windows and statuses (`active`, `rotated`, `revoked`).
   * Compromised keys are cataloged in `src/mcp_india_stack/keys/revocations.json`. Any manifest signed by a revoked key is rejected immediately.
3. **CLI Verification**:
   Verify installed bundled datasets and cache files from the terminal:
   ```bash
   mcp-india-stack --verify-data
   ```
4. **Enforcement Policy**:
   * **Default Mode**: Soft-warns on signature or checksum mismatches in cache, logging warnings and falling back to clean bundled datasets.
   * **Strict Mode (`MCP_INDIA_STACK_REQUIRE_SIGNED_DATA=1`)**: Fails hard (raises `RuntimeError` / `DataLoadError`) if any dataset fails cryptographic signature or checksum verification.

---

## 8. Opt-in Registry Providers (Level A4)

The MCP India Stack defaults to zero-auth, pure offline operation. Level `A4` represents opt-in verification against live registry providers.

When `verify_online=True` is provided to verifying tools (e.g. `validate_gstin(..., verify_online=True)` or `validate_pan(..., verify_online=True)`), the stack queries configured providers protected by:
* SSRF defense (blocking private/loopback/link-local/multicast destinations)
* 3-state Circuit Breaker (fast fail after 5 consecutive errors with 60s cooldown)
* Token-bucket rate limiter per provider
* Strict connect and read timeouts

To write or register custom live providers, refer to the [Writing a Provider Guide](writing_a_provider.md).


