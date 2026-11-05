"""Verification of UIDAI Paperless Offline e-KYC XML artifacts per UIDAI specification."""

from __future__ import annotations

import base64
import datetime
import io
from pathlib import Path
from typing import Any

from mcp_india_stack.authenticity.models import AuthenticityCheck, build_authenticity_envelope
from mcp_india_stack.utils.responses import build_response

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CERTS_DIR = PACKAGE_ROOT / "certs" / "uidai"
DEFAULT_UIDAI_CERT = CERTS_DIR / "uidai_offline_public.pem"


def _check_verify_extras() -> tuple[bool, str | None]:
    """Check whether optional dependencies for verify extra are available."""
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return False, "cryptography"
    return True, None


def _unpack_raw_artifact(
    xml_or_zip_bytes_base64: str, artifact: str, share_code: str | None
) -> str:
    """Unpack input string into raw XML string handling base64 and zip formats."""
    import zipfile

    input_str = xml_or_zip_bytes_base64 or artifact
    raw_str = input_str.strip()
    if not raw_str.startswith("<"):
        try:
            decoded_bytes = base64.b64decode(raw_str)
            if decoded_bytes.startswith(b"PK\x03\x04"):
                with zipfile.ZipFile(io.BytesIO(decoded_bytes)) as zf:
                    pwd = share_code.encode("ascii") if share_code else None
                    xml_files = [n for n in zf.namelist() if n.endswith(".xml")]
                    if xml_files:
                        raw_str = zf.read(xml_files[0], pwd=pwd).decode("utf-8", errors="replace")
            else:
                raw_str = decoded_bytes.decode("utf-8", errors="replace")
        except Exception:
            pass
    return raw_str


def _extract_demographics(root: Any) -> tuple[str, str, str, str, str, dict[str, str]]:
    """Extract masked identifier and non-sensitive demographic fields from XML root."""
    ref_id = root.attrib.get("referenceId", "")
    last_4_digits = ref_id[:4] if len(ref_id) >= 4 else "XXXX"
    masked_aadhaar = f"XXXXXXXX{last_4_digits}"

    poi_elem = root.find(".//Poi")
    poa_elem = root.find(".//Poa")

    name = poi_elem.attrib.get("name", "") if poi_elem is not None else ""
    dob = poi_elem.attrib.get("dob", "") if poi_elem is not None else ""
    gender = poi_elem.attrib.get("gender", "") if poi_elem is not None else ""

    address = {}
    if poa_elem is not None:
        address = {
            "care_of": poa_elem.attrib.get("co", ""),
            "house": poa_elem.attrib.get("house", ""),
            "street": poa_elem.attrib.get("street", ""),
            "locality": poa_elem.attrib.get("loc", ""),
            "vtc": poa_elem.attrib.get("vtc", ""),
            "district": poa_elem.attrib.get("dist", ""),
            "state": poa_elem.attrib.get("state", ""),
            "pincode": poa_elem.attrib.get("pc", ""),
        }
    return ref_id, masked_aadhaar, name, dob, gender, address


def _locate_signature_elements(root: Any) -> tuple[Any, Any]:
    """Locate SignatureValue and SignedInfo elements in XML root."""
    sig_elem = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
    if sig_elem is None:
        sig_elem = root.find(".//Signature")

    sig_val_elem = None
    signed_info_elem = None
    if sig_elem is not None:
        sig_val_elem = sig_elem.find(".//{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        if sig_val_elem is None:
            sig_val_elem = sig_elem.find(".//SignatureValue")
        signed_info_elem = sig_elem.find(".//{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        if signed_info_elem is None:
            signed_info_elem = sig_elem.find(".//SignedInfo")
    return sig_val_elem, signed_info_elem


def _verify_uidai_signature(  # noqa: C901
    root: Any,
    raw_str: str,
    active_cert_path: Path,
    now: datetime.datetime,
    errors: list[str],
    checks: list[AuthenticityCheck],
) -> tuple[bool, bool]:
    """Verify certificate validity and digital signature against trust anchor."""
    import defusedxml.ElementTree as DefusedET
    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    if not active_cert_path.exists():
        errors.append(f"Trust anchor certificate not found at '{active_cert_path}'")
        checks.append(
            AuthenticityCheck(
                name="certificate_validity",
                passed=False,
                level="A3",
                detail=f"Certificate missing: {active_cert_path.name}",
            )
        )
        return False, False

    cert_valid = False
    sig_verified = False

    try:
        cert_bytes = active_cert_path.read_bytes()
        cert = x509.load_pem_x509_certificate(cert_bytes)

        if now < cert.not_valid_before_utc:
            errors.append("UIDAI certificate not yet valid")
            checks.append(
                AuthenticityCheck(
                    name="certificate_validity",
                    passed=False,
                    level="A3",
                    detail="certificate_not_yet_valid",
                )
            )
        elif now > cert.not_valid_after_utc:
            errors.append("UIDAI certificate has expired")
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
                    detail=f"Valid UIDAI trust anchor (SHA256: {fp[:16]}...)",
                )
            )

        sig_val_elem, signed_info_elem = _locate_signature_elements(root)
        if sig_val_elem is None or not (sig_val_elem.text or "").strip():
            errors.append("Signature block missing in offline artifact")
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=False,
                    level="A3",
                    detail="Missing SignatureValue in XML",
                )
            )
        else:
            sig_raw = base64.b64decode(sig_val_elem.text.strip())
            pub_key = cert.public_key()
            if not isinstance(pub_key, rsa.RSAPublicKey):
                raise ValueError("UIDAI trust anchor must be an RSA public key")

            sign_target = None
            start_tag = raw_str.find("<SignedInfo")
            if start_tag != -1:
                end_tag = raw_str.find("</SignedInfo>", start_tag)
                if end_tag != -1:
                    sign_target = raw_str[start_tag : end_tag + len("</SignedInfo>")].encode(
                        "utf-8"
                    )

            if sign_target is None:
                if signed_info_elem is not None:
                    sign_target = DefusedET.tostring(signed_info_elem, encoding="utf-8")
                else:
                    uid_data = root.find(".//UidData")
                    sign_target = (
                        DefusedET.tostring(uid_data, encoding="utf-8")
                        if uid_data is not None
                        else b""
                    )

            pub_key.verify(
                sig_raw,
                sign_target,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            sig_verified = True
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=True,
                    level="A3",
                    detail="UIDAI RSA-2048 XML-DSig signature verified",
                )
            )
    except InvalidSignature:
        errors.append("UIDAI digital signature verification failed")
        checks.append(
            AuthenticityCheck(
                name="uidai_digital_signature",
                passed=False,
                level="A3",
                detail="Invalid RSA XML-DSig signature",
            )
        )
    except Exception as exc:
        errors.append(f"UIDAI signature verification error: {exc}")
        checks.append(
            AuthenticityCheck(
                name="uidai_digital_signature",
                passed=False,
                level="A3",
                detail=str(exc),
            )
        )
    return cert_valid, sig_verified


def verify_aadhaar_offline_artifact(
    xml_or_zip_bytes_base64: str = "",
    *,
    artifact: str = "",
    share_code: str | None = None,
    cert_path: Path | str | None = None,
    current_time: datetime.datetime | None = None,
) -> dict[str, Any]:
    """Verify UIDAI secure offline XML or QR artifact with defusedxml and RSA signature.

    In compliance with DPDP Act 2023:
    1. Extracts reference_id, last 4 digits (NEVER raw 12-digit Aadhaar).
    2. Defends against XML bombs and XXE entity expansions using defusedxml.
    3. Verifies RSA digital signature against UIDAI public trust anchors.
    4. Emits an A3 authenticity envelope.
    """
    has_extras, missing = _check_verify_extras()
    if not has_extras:
        dep_checks = [
            AuthenticityCheck(
                name="dependency_check",
                passed=False,
                level="A0",
                detail=f"Optional extra 'verify' ({missing}) is missing",
            )
        ]
        auth = build_authenticity_envelope(
            valid=False,
            checks=dep_checks,
            source="Unique Identification Authority of India (UIDAI) Offline Paperless e-KYC",
            limitations=["optional extra verify missing"],
        )
        return {
            "success": False,
            "valid": False,
            "error": "optional_dependency_missing",
            "errors": [
                f"Artifact verification requires optional extra 'verify' ({missing} is missing). "
                "Install with: pip install 'mcp-india-stack[verify]'"
            ],
            "required_extra": "verify",
            "authenticity": auth,
        }

    now = current_time or datetime.datetime.now(datetime.timezone.utc)
    checks = []
    errors: list[str] = []

    raw_str = _unpack_raw_artifact(xml_or_zip_bytes_base64, artifact, share_code)

    # 1. Parse safely with defusedxml or bounded parser blocking entities and bombs
    root = None
    has_defused = False
    try:
        import defusedxml.ElementTree as DefusedET

        has_defused = True
    except ImportError:
        pass

    try:
        if has_defused:
            root = DefusedET.fromstring(raw_str)
        else:
            upper_raw = raw_str.upper()
            if "<!DOCTYPE" in upper_raw or "<!ENTITY" in upper_raw:
                raise ValueError("Security violation rejected: XML entity expansion detected")
            import xml.etree.ElementTree as StdET

            root = StdET.fromstring(raw_str)

        checks.append(
            AuthenticityCheck(
                name="xml_schema_and_entity_safety",
                passed=True,
                level="A0",
                detail="XML parsed securely with entity expansion and XXE disabled",
            )
        )
    except Exception as exc:
        is_attack = (
            "EntitiesForbidden" in type(exc).__name__
            or "DefusedXmlException" in type(exc).__name__
            or "Security violation" in str(exc)
            or "<!ENTITY" in raw_str.upper()
            or "<!DOCTYPE" in raw_str.upper()
        )
        if is_attack:
            checks.append(
                AuthenticityCheck(
                    name="xml_schema_and_entity_safety",
                    passed=False,
                    level="A0",
                    detail=f"Security violation rejected: {exc}",
                )
            )
            auth = build_authenticity_envelope(
                valid=False,
                checks=checks,
                source="Unique Identification Authority of India (UIDAI) Offline Paperless e-KYC",
                limitations=["XML bomb or entity expansion attempt rejected"],
            )
            resp = build_response(
                success=False,
                data={"valid": False},
                errors=["XML entity expansion or bomb attack detected"],
                source="offline_signature",
                authenticity=auth,
            )
            resp["valid"] = False
            return resp

        checks.append(
            AuthenticityCheck(
                name="xml_schema_and_entity_safety",
                passed=False,
                level="A0",
                detail=f"Malformed XML: {exc}",
            )
        )
        auth = build_authenticity_envelope(
            valid=False,
            checks=checks,
            source="Unique Identification Authority of India (UIDAI) Offline Paperless e-KYC",
            limitations=["malformed offline artifact"],
        )
        resp = build_response(
            success=False,
            data={"valid": False},
            errors=[f"Failed parsing UIDAI offline artifact: {exc}"],
            source="offline_signature",
            authenticity=auth,
        )
        resp["valid"] = False
        return resp

    ref_id, masked_aadhaar, name, dob, gender, address = _extract_demographics(root)
    last_4 = ref_id[:4] if len(ref_id) >= 4 else "XXXX"
    checks.append(
        AuthenticityCheck(
            name="dpdp_pii_boundary",
            passed=True,
            level="A1",
            detail=f"Identity masked to last 4 digits ({last_4}), raw Aadhaar not stored",
        )
    )

    active_cert_path = Path(cert_path) if cert_path else DEFAULT_UIDAI_CERT
    cert_valid, sig_verified = _verify_uidai_signature(
        root, raw_str, active_cert_path, now, errors, checks
    )

    is_valid = cert_valid and sig_verified and len(errors) == 0
    limitations = [
        "active Aadhaar cancellation or lock status not verified online",
        "biometric match not performed",
    ]
    auth = build_authenticity_envelope(
        valid=is_valid,
        checks=checks,
        source="Unique Identification Authority of India (UIDAI) Offline Paperless e-KYC",
        limitations=limitations,
    )

    data = {
        "valid": is_valid,
        "reference_id": ref_id,
        "masked_aadhaar": masked_aadhaar,
        "name": name,
        "dob": dob,
        "gender": gender,
        "address": address,
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
