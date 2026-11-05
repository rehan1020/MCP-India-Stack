# Trust Anchors & Digital Certificate Registry

This document records the official trust anchors and cryptographic certificates bundled in `mcp-india-stack` for **A3** signed-artifact verification.

---

## 1. Bundled Certificates Registry

| Certificate File | Authority / Purpose | Algorithm | Validity Period | SHA-256 Fingerprint | Primary Source URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `certs/einvoice/nic_einvoice_public.pem` | National Informatics Centre (NIC) / GSTN e-Invoice QR verification | RSA-2048 | 2026–2031 | `0F695E4612F3AABB894DD26F8FA455216D4E47F37036030D967D8186D9C7E5AE` | [NIC e-Invoice Portal](https://einvoice1.gst.gov.in/) |
| `certs/einvoice/nic_einvoice_expired.pem` | NIC e-Invoice Portal (Retired / Rotation Test) | RSA-2048 | Expired | `69D625DC9C0F0DB492E47AAD1B4AF700AF80315533BD191A61FE2C1FB9B4D8EE` | [NIC e-Invoice Portal Archive](https://einvoice1.gst.gov.in/) |
| `certs/uidai/uidai_offline_public.pem` | Unique Identification Authority of India (UIDAI) Paperless Offline e-KYC | RSA-2048 | 2026–2031 | `FF2078FDDA99C30531AC4F52FF27C966AC0949BDDDE4F57338672692224A0137` | [UIDAI Resident Portal](https://uidai.gov.in/) |
| `certs/uidai/uidai_offline_expired.pem` | UIDAI Offline e-KYC (Retired / Rotation Test) | RSA-2048 | Expired | `7E4A702C7AE191CD47144EC863F36261C03430392B156A37B2C6FA53E383E53E` | [UIDAI Developer Portal Archive](https://uidai.gov.in/) |

---

## 2. Certificate Lifecycle & Rotation Policy

1. **Expiry Enforcement**:
   - Every verification operation inspects the X.509 `not_valid_before` and `not_valid_after` timestamps against the current UTC clock.
   - When a supplied certificate has expired, the tool fails gracefully with an explicit `certificate_expired` check failure, rather than crashing or returning an unhandled exception.
2. **Key Rotation**:
   - New certificates issued by NIC or UIDAI are added to the corresponding directory under `src/mcp_india_stack/certs/`.
   - Older certificates remain cataloged to support historical artifact verification with explicit notation.
3. **Offline Trust Model**:
   - All certificates are shipped locally inside the package wheel; no CRL or OCSP calls are made across the network, preserving strict zero-auth offline operation.
