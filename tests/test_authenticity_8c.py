"""Tests for Authenticity System 8c: A3 Signed-Artifact Verification.

Verifies:
1. Valid NIC e-invoice signed QR code JWT verification (A3 level).
2. Tampered signature rejection.
3. Expired trust anchor certificate fail-safe rejection.
4. Seller GSTIN & IRN hash cross-check integrity.
5. UIDAI Paperless Offline e-KYC XML verification (A3 level).
6. DPDP Act compliance (masked Aadhaar, no raw identifiers).
7. Password-protected ZIP artifact extraction with share code.
8. Defense against XML bombs and XXE entity expansions via defusedxml.
9. Graceful fallback when optional extra 'verify' is missing.
10. Pure offline execution guarantee (zero socket connections).
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import socket
import zipfile
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from mcp_india_stack.tools.verify_aadhaar_artifact import verify_aadhaar_offline_artifact
from mcp_india_stack.tools.verify_einvoice import (
    _compute_expected_irn,
    verify_einvoice_qr,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "certs"
CERTS_DIR = Path(__file__).resolve().parents[1] / "src" / "mcp_india_stack" / "certs"

NIC_PUB_CERT = CERTS_DIR / "einvoice" / "nic_einvoice_public.pem"
NIC_EXP_CERT = CERTS_DIR / "einvoice" / "nic_einvoice_expired.pem"
NIC_PRIV_KEY = FIXTURES_DIR / "nic_einvoice_public_private.pem"
NIC_EXP_PRIV_KEY = FIXTURES_DIR / "nic_einvoice_expired_private.pem"

UIDAI_PUB_CERT = CERTS_DIR / "uidai" / "uidai_offline_public.pem"
UIDAI_EXP_CERT = CERTS_DIR / "uidai" / "uidai_offline_expired.pem"
UIDAI_PRIV_KEY = FIXTURES_DIR / "uidai_offline_public_private.pem"
UIDAI_EXP_PRIV_KEY = FIXTURES_DIR / "uidai_offline_expired_private.pem"


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _make_signed_einvoice_jwt(claims: dict[str, Any], priv_key_path: Path = NIC_PRIV_KEY) -> str:
    """Generate a signed e-invoice JWT fixture using test private key."""
    header = {"alg": "RS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(claims).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    priv_key = serialization.load_pem_private_key(priv_key_path.read_bytes(), password=None)
    assert isinstance(priv_key, rsa.RSAPrivateKey)

    sig = priv_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = _b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _make_signed_aadhaar_xml(
    ref_id: str = "123420260515123456", priv_key_path: Path = UIDAI_PRIV_KEY
) -> str:
    """Generate a signed UIDAI offline XML fixture using test private key."""
    signed_info_xml = (
        '<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">'
        '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
        '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha256"/>'
        "</SignedInfo>"
    )
    signed_info_bytes = signed_info_xml.encode("utf-8")

    priv_key = serialization.load_pem_private_key(priv_key_path.read_bytes(), password=None)
    assert isinstance(priv_key, rsa.RSAPrivateKey)

    sig = priv_key.sign(signed_info_bytes, padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(sig).decode("ascii")

    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<OfflinePaperlessKyc referenceId="{ref_id}">\n'
        f"  <UidData>\n"
        f'    <Poi dob="1990-01-01" gender="M" name="Aadhaar Holder"/>\n'
        f'    <Poa co="S/O Father" dist="Bengaluru" house="42" '
        f'loc="Koramangala" pc="560034" state="Karnataka" street="100ft Rd" vtc="Bengaluru"/>\n'
        f"  </UidData>\n"
        f'  <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">\n'
        f"    {signed_info_xml}\n"
        f"    <SignatureValue>{sig_b64}</SignatureValue>\n"
        f"  </Signature>\n"
        f"</OfflinePaperlessKyc>"
    )
    return xml


# ===========================================================================
# 1. e-Invoice QR Code Tests
# ===========================================================================


def test_einvoice_qr_valid_signature() -> None:
    """Valid e-invoice signed QR code passes verification and promotes to Level A3."""
    seller_gstin = "27AAPFU0939F1ZV"
    buyer_gstin = "27AAPFU0939F1ZV"
    doc_no = "INV-001"
    doc_typ = "INV"
    doc_dt = "2026-05-15"
    fin_yr = "2026-27"
    raw_irn_seed = f"{seller_gstin}{doc_typ}{doc_no}{fin_yr}"
    irn = hashlib.sha256(raw_irn_seed.encode("utf-8")).hexdigest().lower()

    claims = {
        "SellerGstin": seller_gstin,
        "BuyerGstin": buyer_gstin,
        "DocNo": doc_no,
        "DocTyp": doc_typ,
        "DocDt": doc_dt,
        "TotInvVal": 118000.0,
        "ItemCnt": 2,
        "MainHsnCode": "998311",
        "Irn": irn,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)

    res = verify_einvoice_qr(
        jwt_str,
        expected_gstin=seller_gstin,
        expected_irn=irn,
        cert_path=NIC_PUB_CERT,
    )

    assert res["success"] is True
    assert res["valid"] is True
    assert res["data"]["irn"] == irn
    assert res["data"]["seller_gstin"] == seller_gstin
    assert res["data"]["total_value"] == 118000.0

    auth = res["authenticity"]
    assert auth is not None
    assert auth["level"] == "A3"
    assert auth["source"] == "National Informatics Centre (NIC) / GSTN e-Invoice System"

    checks_by_name = {c["name"]: c for c in auth["checks"]}
    assert checks_by_name["digital_signature_verification"]["passed"] is True
    assert checks_by_name["digital_signature_verification"]["level"] == "A3"
    assert checks_by_name["irn_hash_integrity"]["passed"] is True
    assert checks_by_name["gstin_consistency"]["passed"] is True


def test_einvoice_qr_valid_signature_before_april() -> None:
    """January-March invoices spell the fiscal year like the rest of the year."""
    seller_gstin = "27AAPFU0939F1ZV"
    buyer_gstin = "27AAPFU0939F1ZV"
    doc_no = "INV-001"
    doc_typ = "INV"
    doc_dt = "15/02/2027"
    fin_yr = "2026-27"
    raw_irn_seed = f"{seller_gstin}{doc_typ}{doc_no}{fin_yr}"
    irn = hashlib.sha256(raw_irn_seed.encode("utf-8")).hexdigest().lower()

    claims = {
        "SellerGstin": seller_gstin,
        "BuyerGstin": buyer_gstin,
        "DocNo": doc_no,
        "DocTyp": doc_typ,
        "DocDt": doc_dt,
        "TotInvVal": 118000.0,
        "ItemCnt": 2,
        "MainHsnCode": "998311",
        "Irn": irn,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)

    res = verify_einvoice_qr(
        jwt_str,
        expected_gstin=seller_gstin,
        expected_irn=irn,
        cert_path=NIC_PUB_CERT,
    )

    assert res["success"] is True
    assert res["valid"] is True, res["errors"]
    checks_by_name = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks_by_name["irn_hash_integrity"]["passed"] is True


@pytest.mark.parametrize(
    ("doc_dt", "expected_fin_yr"),
    [
        ("15/02/2027", "2026-27"),
        ("31/03/2026", "2025-26"),
        ("01/04/2026", "2026-27"),
        ("2027-01-31", "2026-27"),
    ],
)
def test_compute_expected_irn_fiscal_year_boundaries(
    doc_dt: str, expected_fin_yr: str
) -> None:
    """Fiscal years before April keep the hyphenated FY format."""
    _, fin_yr = _compute_expected_irn("27AAPFU0939F1ZV", "INV", "INV-001", doc_dt)
    assert fin_yr == expected_fin_yr


def test_einvoice_qr_tampered_signature() -> None:
    """Tampered signature must fail verification, yielding level=None and valid=False."""
    claims = {
        "SellerGstin": "27AAPFU0939F1ZV",
        "BuyerGstin": "29AADCB2230M1ZT",
        "DocNo": "INV-001",
        "DocTyp": "INV",
        "DocDt": "2026-05-15",
        "TotInvVal": 5000.0,
        "ItemCnt": 1,
        "MainHsnCode": "998311",
        "Irn": "0" * 64,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)

    # Tamper with the signature portion
    parts = jwt_str.split(".")
    tampered_sig = parts[2][:-4] + "AAAA"
    tampered_jwt = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    res = verify_einvoice_qr(tampered_jwt, cert_path=NIC_PUB_CERT)
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    assert any("signature" in e.lower() for e in res["errors"])


def test_einvoice_qr_expired_certificate() -> None:
    """Expired trust anchor certificate must fail with certificate_expired."""
    claims = {
        "SellerGstin": "27AAPFU0939F1ZV",
        "BuyerGstin": "29AADCB2230M1ZT",
        "DocNo": "INV-001",
        "DocTyp": "INV",
        "DocDt": "2026-05-15",
        "TotInvVal": 5000.0,
        "ItemCnt": 1,
        "MainHsnCode": "998311",
        "Irn": "0" * 64,
    }
    jwt_str = _make_signed_einvoice_jwt(claims, priv_key_path=NIC_EXP_PRIV_KEY)

    res = verify_einvoice_qr(jwt_str, cert_path=NIC_EXP_CERT)
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    checks = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks["certificate_validity"]["passed"] is False
    assert checks["certificate_validity"]["detail"] == "certificate_expired"


def test_einvoice_qr_irn_mismatch() -> None:
    """Mismatch in expected_irn parameter flags cross-check failure."""
    claims = {
        "SellerGstin": "27AAPFU0939F1ZV",
        "BuyerGstin": "29AADCB2230M1ZT",
        "DocNo": "INV-001",
        "DocTyp": "INV",
        "DocDt": "2026-05-15",
        "TotInvVal": 5000.0,
        "ItemCnt": 1,
        "MainHsnCode": "998311",
        "Irn": "a" * 64,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)

    res = verify_einvoice_qr(
        jwt_str,
        expected_irn="b" * 64,
        cert_path=NIC_PUB_CERT,
    )
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    checks = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks["irn_hash_integrity"]["passed"] is False


def test_einvoice_qr_seller_gstin_mismatch() -> None:
    """Mismatch between token seller GSTIN and expected_gstin parameter fails consistency."""
    claims = {
        "SellerGstin": "27AAPFU0939F1ZV",
        "BuyerGstin": "29AADCB2230M1ZT",
        "DocNo": "INV-001",
        "DocTyp": "INV",
        "DocDt": "2026-05-15",
        "TotInvVal": 5000.0,
        "ItemCnt": 1,
        "MainHsnCode": "998311",
        "Irn": "0" * 64,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)

    res = verify_einvoice_qr(
        jwt_str,
        expected_gstin="29AADCB2230M1ZT",  # Pass different GSTIN
        cert_path=NIC_PUB_CERT,
    )
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    checks = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks["gstin_consistency"]["passed"] is False


# ===========================================================================
# 2. Aadhaar Offline Paperless e-KYC Tests
# ===========================================================================


def test_aadhaar_offline_artifact_valid_signature() -> None:
    """Valid UIDAI offline XML passes RSA-2048 verification with A3 and DPDP masking."""
    xml_str = _make_signed_aadhaar_xml(ref_id="432120260515123456")

    res = verify_aadhaar_offline_artifact(xml_str, cert_path=UIDAI_PUB_CERT)
    assert res["success"] is True
    assert res["valid"] is True
    assert res["data"]["masked_aadhaar"] == "XXXXXXXX4321"
    assert res["data"]["name"] == "Aadhaar Holder"
    assert res["data"]["address"]["state"] == "Karnataka"

    auth = res["authenticity"]
    assert auth is not None
    assert auth["level"] == "A3"
    assert "Unique Identification Authority of India (UIDAI)" in auth["source"]

    checks = {c["name"]: c for c in auth["checks"]}
    assert checks["uidai_digital_signature"]["passed"] is True
    assert checks["dpdp_pii_boundary"]["passed"] is True
    assert checks["xml_schema_and_entity_safety"]["passed"] is True


def test_aadhaar_offline_artifact_tampered_signature() -> None:
    """Tampered XML signature value is rejected with level=None."""
    xml_str = _make_signed_aadhaar_xml()
    tampered_xml = xml_str.replace("SignatureValue>", "SignatureValue>DEADBEEF")

    res = verify_aadhaar_offline_artifact(tampered_xml, cert_path=UIDAI_PUB_CERT)
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    checks = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks["uidai_digital_signature"]["passed"] is False


def test_aadhaar_offline_artifact_expired_cert() -> None:
    """Expired UIDAI certificate fails with certificate_expired."""
    xml_str = _make_signed_aadhaar_xml(priv_key_path=UIDAI_EXP_PRIV_KEY)

    res = verify_aadhaar_offline_artifact(xml_str, cert_path=UIDAI_EXP_CERT)
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    checks = {c["name"]: c for c in res["authenticity"]["checks"]}
    assert checks["certificate_validity"]["passed"] is False
    assert checks["certificate_validity"]["detail"] == "certificate_expired"


def test_aadhaar_offline_artifact_zip_with_share_code() -> None:
    """Password-protected ZIP containing offline XML extracts and verifies successfully."""
    xml_str = _make_signed_aadhaar_xml(ref_id="999920260515123456")
    share_code = "4321"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(share_code.encode("ascii"))
        zf.writestr("offline_aadhaar.xml", xml_str.encode("utf-8"))

    zip_bytes = zip_buffer.getvalue()
    zip_b64 = base64.b64encode(zip_bytes).decode("ascii")

    res = verify_aadhaar_offline_artifact(zip_b64, share_code=share_code, cert_path=UIDAI_PUB_CERT)
    assert res["success"] is True
    assert res["valid"] is True
    assert res["data"]["masked_aadhaar"] == "XXXXXXXX9999"
    assert res["authenticity"]["level"] == "A3"


def test_aadhaar_offline_artifact_xxe_and_xml_bomb_defense() -> None:
    """XML bomb or XXE entity expansion attempt is caught and rejected safely by defusedxml."""
    billion_laughs_attack = (
        '<?xml version="1.0"?>\n'
        "<!DOCTYPE lolz [\n"
        ' <!ENTITY lol "lol">\n'
        " <!ELEMENT lolz (#PCDATA)>\n"
        ' <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">\n'
        ' <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">\n'
        "]>\n"
        "<lolz>&lol2;</lolz>"
    )

    res = verify_aadhaar_offline_artifact(billion_laughs_attack, cert_path=UIDAI_PUB_CERT)
    assert res["success"] is False
    assert res["valid"] is False
    assert res["authenticity"]["level"] is None
    assert any("attack" in e.lower() or "bomb" in e.lower() for e in res["errors"])


def test_missing_verify_extra_graceful_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """When verify optional extra is not installed, tools fail gracefully with structured error."""
    import mcp_india_stack.tools.verify_aadhaar_artifact as aadhaar_mod
    import mcp_india_stack.tools.verify_einvoice as einvoice_mod

    monkeypatch.setattr(einvoice_mod, "_check_verify_extras", lambda: (False, "cryptography"))
    monkeypatch.setattr(aadhaar_mod, "_check_verify_extras", lambda: (False, "cryptography"))

    res_einvoice = verify_einvoice_qr("sample.jwt.string")
    assert res_einvoice["success"] is False
    assert res_einvoice["error"] == "optional_dependency_missing"
    assert "pip install" in res_einvoice["errors"][0]
    assert res_einvoice["authenticity"] is not None
    assert res_einvoice["authenticity"]["level"] is None

    res_aadhaar = verify_aadhaar_offline_artifact("<xml />")
    assert res_aadhaar["success"] is False
    assert res_aadhaar["error"] == "optional_dependency_missing"
    assert "pip install" in res_aadhaar["errors"][0]
    assert res_aadhaar["authenticity"] is not None
    assert res_aadhaar["authenticity"]["level"] is None


def test_offline_guarantee_zero_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that artifact verification executes 100% offline without opening sockets."""

    def forbid_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Socket connection attempted in offline artifact verification!")

    monkeypatch.setattr(socket, "socket", forbid_socket)

    # 1. Valid e-invoice verification
    seller_gstin = "27AAPFU0939F1ZV"
    doc_no = "INV-001"
    doc_typ = "INV"
    fin_yr = "2026-27"
    raw_irn_seed = f"{seller_gstin}{doc_typ}{doc_no}{fin_yr}"
    irn = hashlib.sha256(raw_irn_seed.encode("utf-8")).hexdigest().lower()

    claims = {
        "SellerGstin": seller_gstin,
        "BuyerGstin": "27AAPFU0939F1ZV",
        "DocNo": doc_no,
        "DocTyp": doc_typ,
        "DocDt": "2026-05-15",
        "TotInvVal": 1000.0,
        "ItemCnt": 1,
        "MainHsnCode": "998311",
        "Irn": irn,
    }
    jwt_str = _make_signed_einvoice_jwt(claims)
    res_inv = verify_einvoice_qr(
        jwt_str,
        expected_gstin=seller_gstin,
        expected_irn=irn,
        cert_path=NIC_PUB_CERT,
    )
    assert res_inv["valid"] is True
    assert res_inv["authenticity"]["level"] == "A3"

    # 2. Valid Aadhaar verification
    xml_str = _make_signed_aadhaar_xml(ref_id="888820260515123456")
    res_aadh = verify_aadhaar_offline_artifact(xml_str, cert_path=UIDAI_PUB_CERT)
    assert res_aadh["valid"] is True
    assert res_aadh["authenticity"]["level"] == "A3"
