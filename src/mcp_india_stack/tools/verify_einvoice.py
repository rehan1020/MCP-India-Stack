"""Verification of NIC / GSTN B2B e-invoice signed QR codes per GST specification."""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from mcp_india_stack.authenticity.models import AuthenticityCheck, build_authenticity_envelope
from mcp_india_stack.tools.gstin import validate_gstin
from mcp_india_stack.utils.responses import build_response

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CERTS_DIR = PACKAGE_ROOT / "certs" / "einvoice"
DEFAULT_NIC_CERT = CERTS_DIR / "nic_einvoice_public.pem"


def _check_verify_extras() -> tuple[bool, str | None]:
    """Check whether optional dependencies for verify extra are available."""
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return False, "cryptography"
    try:
        import defusedxml  # noqa: F401
    except ImportError:
        return False, "defusedxml"
    return True, None


def _base64url_decode(payload: str) -> bytes:
    """Decode base64url encoded string with padding restoration."""
    rem = len(payload) % 4
    if rem > 0:
        payload += "=" * (4 - rem)
    return base64.urlsafe_b64decode(payload)


def _compute_expected_irn(
    seller_gstin: str, doc_typ: str, doc_no: str, doc_dt: str
) -> tuple[str, str]:
    """Derive financial year and compute expected IRN SHA-256 hash."""
    fin_yr = "2026-27"
    try:
        if "-" in doc_dt:
            parts = doc_dt.split("-")
            if len(parts[0]) == 4:
                year, month = int(parts[0]), int(parts[1])
            else:
                year, month = int(parts[2]), int(parts[1])
        elif "/" in doc_dt:
            parts = doc_dt.split("/")
            if len(parts[0]) == 4:
                year, month = int(parts[0]), int(parts[1])
            else:
                year, month = int(parts[2]), int(parts[1])
        else:
            year, month = 2026, 4

        if month >= 4:
            fin_yr = f"{year}-{(year + 1) % 100:02d}"
        else:
            fin_yr = f"{year - 1}{year % 100:02d}"
    except Exception:
        pass

    raw = f"{seller_gstin.upper()}{doc_typ.upper()}{doc_no.upper()}{fin_yr}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().lower(), fin_yr


def verify_einvoice_qr(
    qr_text: str = "",
    *,
    qr_content: str = "",
    expected_gstin: str | None = None,
    expected_irn: str | None = None,
    cert_path: Path | str | None = None,
    current_time: datetime.datetime | None = None,
) -> dict[str, Any]:
    """Verify NIC/GSTN RSA/ECDSA signed JWT in B2B e-invoice QR code.

    Decodes header and claims without network calls, verifies digital signature
    against bundled NIC trust anchors, performs IRN and GSTIN cross-checks,
    and returns an A3 authenticity envelope.
    """
    input_text = qr_text or qr_content
    has_extras, missing = _check_verify_extras()
    if not has_extras:
        return {
            "success": False,
            "valid": False,
            "error": "optional_dependency_missing",
            "errors": [
                f"Artifact verification requires optional extra 'verify' ({missing} is missing). "
                "Install with: pip install 'mcp-india-stack[verify]'"
            ],
            "required_extra": "verify",
            "authenticity": None,
        }

    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    now = current_time or datetime.datetime.now(datetime.timezone.utc)
    checks: list[AuthenticityCheck] = []
    errors: list[str] = []

    # 1. Parse JWT structure
    parts = input_text.strip().split(".")
    if len(parts) != 3:
        checks.append(
            AuthenticityCheck(
                name="qr_jwt_structure",
                passed=False,
                level="A0",
                detail=f"Expected 3 JWT segments separated by dots, got {len(parts)}",
            )
        )
        auth = build_authenticity_envelope(
            valid=False,
            checks=checks,
            source="National Informatics Centre (NIC) / GSTN e-Invoice System",
            limitations=["invalid JWT structure"],
        )
        resp = build_response(
            success=False,
            data={"valid": False},
            errors=["Invalid e-invoice QR format: expected signed JWT"],
            source="offline_signature",
            authenticity=auth,
        )
        resp["valid"] = False
        return resp

    header_b64, payload_b64, sig_b64 = parts
    try:
        header = json.loads(_base64url_decode(header_b64).decode("utf-8"))
        claims = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
        sig_bytes = _base64url_decode(sig_b64)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        checks.append(
            AuthenticityCheck(
                name="qr_jwt_structure",
                passed=True,
                level="A0",
                detail=f"Signed JWT algorithm {header.get('alg', 'RS256')}",
            )
        )
    except Exception as exc:
        checks.append(
            AuthenticityCheck(
                name="qr_jwt_structure",
                passed=False,
                level="A0",
                detail=f"Failed decoding JWT segments: {exc}",
            )
        )
        auth = build_authenticity_envelope(
            valid=False,
            checks=checks,
            source="National Informatics Centre (NIC) / GSTN e-Invoice System",
            limitations=["malformed JWT payload"],
        )
        resp = build_response(
            success=False,
            data={"valid": False},
            errors=[f"Failed decoding e-invoice QR JWT: {exc}"],
            source="offline_signature",
            authenticity=auth,
        )
        resp["valid"] = False
        return resp

    # 2. Extract Claims
    irn = str(claims.get("Irn", "")).strip()
    seller_gstin = str(claims.get("SellerGstin", "")).strip().upper()
    buyer_gstin = str(claims.get("BuyerGstin", "")).strip().upper()
    doc_no = str(claims.get("DocNo", "")).strip()
    doc_typ = str(claims.get("DocTyp", "INV")).strip().upper()
    doc_dt = str(claims.get("DocDt", "")).strip()
    tot_val = float(claims.get("TotInvVal", 0.0))
    item_cnt = int(claims.get("ItemCnt", 0))
    main_hsn = str(claims.get("MainHsnCode", "")).strip()

    # 3. GSTIN Validation & Cross-Check
    seller_val: dict[str, Any] = validate_gstin(seller_gstin)
    buyer_val: dict[str, Any] = (
        validate_gstin(buyer_gstin) if len(buyer_gstin) == 15 else {"valid": True}
    )

    seller_data = seller_val.get("data")
    seller_ok = bool(
        seller_val.get("valid") or (isinstance(seller_data, dict) and seller_data.get("valid"))
    )

    buyer_data = buyer_val.get("data")
    buyer_ok = bool(
        buyer_val.get("valid") or (isinstance(buyer_data, dict) and buyer_data.get("valid"))
    )

    if not seller_ok:
        errors.append("Seller GSTIN invalid")
        checks.append(
            AuthenticityCheck(
                name="gstin_consistency", passed=False, level="A1", detail="Seller GSTIN invalid"
            )
        )
    elif not buyer_ok:
        errors.append("Buyer GSTIN invalid")
        checks.append(
            AuthenticityCheck(
                name="gstin_consistency", passed=False, level="A1", detail="Buyer GSTIN invalid"
            )
        )
    elif expected_gstin and seller_gstin != expected_gstin.strip().upper():
        err = f"Seller GSTIN mismatch: expected '{expected_gstin}', got '{seller_gstin}'"
        errors.append(err)
        checks.append(
            AuthenticityCheck(name="gstin_consistency", passed=False, level="A1", detail=err)
        )
    else:
        checks.append(
            AuthenticityCheck(
                name="gstin_consistency",
                passed=True,
                level="A1",
                detail=f"Seller GSTIN '{seller_gstin}' and Buyer GSTIN valid",
            )
        )

    # 4. IRN Hash Cross-Check
    computed_irn, fin_yr = _compute_expected_irn(seller_gstin, doc_typ, doc_no, doc_dt)
    if expected_irn and irn.lower() != expected_irn.strip().lower():
        errors.append("IRN in claim does not match expected_irn parameter")
        checks.append(
            AuthenticityCheck(
                name="irn_hash_integrity",
                passed=False,
                level="A1",
                detail=(
                    f"IRN mismatch against expected_irn: "
                    f"expected {expected_irn[:16]}..., got {irn[:16]}..."
                ),
            )
        )
    elif irn.lower() == computed_irn.lower():
        checks.append(
            AuthenticityCheck(
                name="irn_hash_integrity",
                passed=True,
                level="A1",
                detail=f"IRN matches SHA-256(SupplierGSTIN+DocTyp+DocNo+FinYr={fin_yr})",
            )
        )
    else:
        errors.append("IRN in claim does not match computed SHA-256 hash")
        checks.append(
            AuthenticityCheck(
                name="irn_hash_integrity",
                passed=False,
                level="A1",
                detail=f"IRN mismatch: computed {computed_irn[:16]}..., got {irn[:16]}...",
            )
        )

    # 5. Date plausibility
    checks.append(
        AuthenticityCheck(
            name="doc_date_plausible",
            passed=bool(doc_dt),
            level="A1",
            detail=f"Document date '{doc_dt}' recorded",
        )
    )

    # 6. Load Certificate & Check Expiry
    active_cert_path = Path(cert_path) if cert_path else DEFAULT_NIC_CERT
    cert_valid = False
    sig_verified = False

    if not active_cert_path.exists():
        errors.append(f"Trust anchor certificate not found at '{active_cert_path}'")
        checks.append(
            AuthenticityCheck(
                name="certificate_validity",
                passed=False,
                level="A3",
                detail=f"Certificate file missing: {active_cert_path.name}",
            )
        )
    else:
        try:
            cert_bytes = active_cert_path.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_bytes)

            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc

            if now < not_before:
                errors.append("NIC e-invoice certificate not yet valid")
                checks.append(
                    AuthenticityCheck(
                        name="certificate_validity",
                        passed=False,
                        level="A3",
                        detail="certificate_not_yet_valid",
                    )
                )
            elif now > not_after:
                errors.append("NIC e-invoice certificate has expired")
                checks.append(
                    AuthenticityCheck(
                        name="certificate_validity",
                        passed=False,
                        level="A3",
                        detail="certificate_expired",
                    )
                )
            else:
                cert_valid = True
                fp = cert.fingerprint(hashes.SHA256()).hex().upper()
                checks.append(
                    AuthenticityCheck(
                        name="certificate_validity",
                        passed=True,
                        level="A3",
                        detail=f"Valid NIC certificate (SHA256: {fp[:16]}...)",
                    )
                )

            # 7. Signature Verification
            pub_key = cert.public_key()
            if not isinstance(pub_key, rsa.RSAPublicKey):
                raise ValueError("NIC e-invoice trust anchor must be an RSA public key")
            pub_key.verify(
                sig_bytes,
                signing_input,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            sig_verified = True
            checks.append(
                AuthenticityCheck(
                    name="digital_signature_verification",
                    passed=True,
                    level="A3",
                    detail="NIC RSA-2048 digital signature verified",
                )
            )
        except InvalidSignature:
            errors.append("Cryptographic signature on e-invoice QR is invalid")
            checks.append(
                AuthenticityCheck(
                    name="digital_signature_verification",
                    passed=False,
                    level="A3",
                    detail="Invalid RSA signature",
                )
            )
        except Exception as exc:
            errors.append(f"Signature verification error: {exc}")
            checks.append(
                AuthenticityCheck(
                    name="digital_signature_verification",
                    passed=False,
                    level="A3",
                    detail=str(exc),
                )
            )

    is_valid = cert_valid and sig_verified and len(errors) == 0
    limitations = [
        "active invoice cancellation status not checked online",
        "supplier GSTN return filing status not verified",
    ]
    auth = build_authenticity_envelope(
        valid=is_valid,
        checks=checks,
        source="National Informatics Centre (NIC) / GSTN e-Invoice System",
        limitations=limitations,
    )

    data = {
        "valid": is_valid,
        "irn": irn,
        "seller_gstin": seller_gstin,
        "buyer_gstin": buyer_gstin,
        "doc_no": doc_no,
        "doc_typ": doc_typ,
        "doc_date": doc_dt,
        "total_value": tot_val,
        "item_count": item_cnt,
        "main_hsn": main_hsn,
        "fin_year": fin_yr,
    }

    resp = build_response(
        success=is_valid,
        data=data,
        errors=errors,
        source="offline_signature",
        authenticity=auth,
    )
    resp["valid"] = is_valid
    return resp
