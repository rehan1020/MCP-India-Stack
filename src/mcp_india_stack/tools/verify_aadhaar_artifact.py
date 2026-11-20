"""Verification of UIDAI Paperless Offline e-KYC XML artifacts per UIDAI specification."""

from __future__ import annotations

import base64
import datetime
import io
import xml.etree.ElementTree as ET
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


def _extract_demographics(
    verified_node: Any, doc_root: Any = None
) -> tuple[str, str, str, str, str, dict[str, str]]:
    """Extract masked identifier and non-sensitive demographic fields from verified XML node."""
    if verified_node is None:
        return "", "", "", "", "", {}

    # Extract referenceId from verified node if available, otherwise from document root
    ref_id = ""
    if hasattr(verified_node, "attrib"):
        ref_id = verified_node.attrib.get("referenceId", "")
    elif hasattr(verified_node, "get"):
        ref_id = verified_node.get("referenceId", "")

    if not ref_id and doc_root is not None:
        if hasattr(doc_root, "attrib"):
            ref_id = doc_root.attrib.get("referenceId", "")
        elif hasattr(doc_root, "get"):
            ref_id = doc_root.get("referenceId", "")

    last_4_digits = ref_id[:4] if len(ref_id) >= 4 else "XXXX"
    masked_aadhaar = f"XXXXXXXX{last_4_digits}"

    poi_elem = None
    poa_elem = None
    if hasattr(verified_node, "xpath"):
        poi_nodes = verified_node.xpath(".//*[local-name()='Poi']")
        poi_elem = poi_nodes[0] if poi_nodes else None
        poa_nodes = verified_node.xpath(".//*[local-name()='Poa']")
        poa_elem = poa_nodes[0] if poa_nodes else None
    elif hasattr(verified_node, "find"):
        poi_elem = verified_node.find(".//Poi")
        poa_elem = verified_node.find(".//Poa")

    name = ""
    dob = ""
    gender = ""
    if poi_elem is not None:
        get_poi = getattr(poi_elem, "attrib", poi_elem)
        name = get_poi.get("name", "")
        dob = get_poi.get("dob", "")
        gender = get_poi.get("gender", "")

    address: dict[str, str] = {}
    if poa_elem is not None:
        get_poa = getattr(poa_elem, "attrib", poa_elem)
        address = {
            "care_of": get_poa.get("co", ""),
            "house": get_poa.get("house", ""),
            "street": get_poa.get("street", ""),
            "locality": get_poa.get("loc", ""),
            "vtc": get_poa.get("vtc", ""),
            "district": get_poa.get("dist", ""),
            "state": get_poa.get("state", ""),
            "pincode": get_poa.get("pc", ""),
        }
    return ref_id, masked_aadhaar, name, dob, gender, address


def _verify_with_signxml(raw_str: str, cert_bytes: bytes) -> tuple[bool, Any, str | None]:
    """Verify XML signature using signxml library with digest and scope enforcement."""
    import signxml
    from lxml import etree
    from signxml.verifier import XMLVerifier

    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)
        doc = etree.fromstring(raw_str.encode("utf-8"), parser=parser)

        sig_methods = doc.xpath("//*[local-name()='SignatureMethod']")
        if not sig_methods:
            return False, None, "Missing SignatureMethod in SignedInfo"
        sig_alg = sig_methods[0].get("Algorithm", "")
        allowed_sig_algs = {
            "http://www.w3.org/2000/09/xmldsig#rsa-sha256",
            "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        }
        if sig_alg not in allowed_sig_algs:
            return False, None, f"Forbidden or unsupported signature algorithm: {sig_alg}"

        verifier = XMLVerifier()
        cert_str = cert_bytes.decode("utf-8")
        result = verifier.verify(doc, x509_cert=cert_str)
        verified_xml = result[0].signed_xml if isinstance(result, list) else result.signed_xml

        if verified_xml is None:
            return False, None, "Verified XML element is empty"

        verified_uid = None
        if verified_xml.tag.endswith("UidData"):
            verified_uid = verified_xml
        else:
            u_nodes = verified_xml.xpath(".//*[local-name()='UidData']")
            if u_nodes:
                verified_uid = u_nodes[0]

        if verified_uid is None:
            return (
                False,
                None,
                "Cryptographic verification failed: <UidData> is not covered by "
                "verified signature reference",
            )

        return True, verified_xml, None
    except signxml.exceptions.InvalidDigest as exc:
        return (
            False,
            None,
            f"UIDAI artifact digest mismatch: signed data was modified after signing ({exc})",
        )
    except signxml.exceptions.InvalidSignature as exc:
        return False, None, f"UIDAI digital signature verification failed: {exc}"
    except Exception:
        # Fall back to builtin verifier if signxml encountered an unsupported XML structure
        return _verify_with_builtin(raw_str, cert_bytes)


def _parse_signature_structure(
    root: Any,
) -> tuple[Any | None, Any | None, str, list[Any], str | None]:
    """Extract and validate Signature, SignedInfo, and SignatureValue structure."""
    ds_signatures = root.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
    if not ds_signatures:
        ds_signatures = [e for e in root.iter() if e.tag.endswith("Signature")]
    if len(ds_signatures) == 0:
        return None, None, "", [], "Signature block missing in offline artifact"
    if len(ds_signatures) > 1:
        return (
            None,
            None,
            "",
            [],
            "Security violation: multiple Signature elements detected (signature wrapping defense)",
        )

    sig_elem = ds_signatures[0]
    signed_info_elem = None
    sig_val_elem = None
    for child in sig_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "SignedInfo":
            signed_info_elem = child
        elif tag == "SignatureValue":
            sig_val_elem = child

    if signed_info_elem is None:
        return None, None, "", [], "SignedInfo element missing in Signature"
    if sig_val_elem is None or not (sig_val_elem.text or "").strip():
        return None, None, "", [], "Missing SignatureValue in XML"

    sig_method = ""
    references = []
    for child in signed_info_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "SignatureMethod":
            sig_method = child.attrib.get("Algorithm", "")
        elif tag == "Reference":
            references.append(child)

    allowed_sig_algs = {
        "http://www.w3.org/2000/09/xmldsig#rsa-sha256",
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    }
    if sig_method not in allowed_sig_algs:
        return (
            None,
            None,
            "",
            [],
            f"Forbidden or unsupported SignatureMethod algorithm: {sig_method}",
        )

    if not references:
        return None, None, "", [], "No Reference elements found in SignedInfo"

    return signed_info_elem, sig_val_elem, sig_method, references, None


def _canonicalize_target(
    uri: str, root: Any, raw_str: str
) -> tuple[bytes | None, Any | None, str | None]:
    """Canonicalize referenced target node and return its element."""
    import copy

    if uri == "":
        try:
            from lxml import etree as lx_etree

            clean_lx = lx_etree.fromstring(raw_str.encode("utf-8"))
            for s in clean_lx.xpath("//*[local-name()='Signature']"):
                s.getparent().remove(s)
            c14n_bytes = lx_etree.tostring(clean_lx, method="c14n")
        except Exception:
            clean_doc = copy.deepcopy(root)
            for s in list(clean_doc):
                if s.tag.endswith("Signature"):
                    clean_doc.remove(s)
            c14n_bytes = ET.canonicalize(ET.tostring(clean_doc, encoding="utf-8")).encode("utf-8")
        return c14n_bytes, root, None

    if uri.startswith("#"):
        target_id = uri[1:]
        target_node = None
        for elem in root.iter():
            if target_id in (
                elem.attrib.get("Id"),
                elem.attrib.get("id"),
                elem.attrib.get("referenceId"),
            ):
                target_node = elem
                break
        if target_node is None:
            return None, None, f"Reference URI '{uri}' could not be resolved"
        c14n_bytes = ET.canonicalize(ET.tostring(target_node, encoding="utf-8")).encode("utf-8")
        return c14n_bytes, target_node, None

    return None, None, f"Unsupported Reference URI: '{uri}'"


def _verify_reference_digest(
    ref: Any, root: Any, raw_str: str
) -> tuple[bool, Any | None, str | None]:
    """Verify digest value of a single Reference element against canonicalized data."""
    import hashlib
    import hmac

    uri = ref.attrib.get("URI", "")
    digest_method_elem = None
    digest_val_elem = None
    for r_child in ref:
        r_tag = r_child.tag.split("}")[-1] if "}" in r_child.tag else r_child.tag
        if r_tag == "DigestMethod":
            digest_method_elem = r_child
        elif r_tag == "DigestValue":
            digest_val_elem = r_child

    if digest_method_elem is None:
        return False, None, "DigestMethod missing in Reference"
    if digest_val_elem is None or not (digest_val_elem.text or "").strip():
        return False, None, "DigestValue missing or empty in Reference"

    digest_alg = digest_method_elem.attrib.get("Algorithm", "")
    allowed_digest_algs = {
        "http://www.w3.org/2000/09/xmldsig#sha256",
        "http://www.w3.org/2001/04/xmlenc#sha256",
    }
    if digest_alg not in allowed_digest_algs:
        return False, None, f"Forbidden or unsupported DigestMethod algorithm: {digest_alg}"

    expected_digest_b64 = digest_val_elem.text.strip()
    try:
        expected_digest = base64.b64decode(expected_digest_b64)
    except Exception:
        return False, None, "Invalid base64 in DigestValue"

    c14n_bytes, target_node, err = _canonicalize_target(uri, root, raw_str)
    if err or c14n_bytes is None or target_node is None:
        return False, None, err

    computed_digest = hashlib.sha256(c14n_bytes).digest()
    if not hmac.compare_digest(expected_digest, computed_digest):
        return (
            False,
            None,
            "UIDAI artifact digest mismatch: signed data was modified after signing",
        )

    return True, target_node, None


def _verify_signed_info_rsa(
    signed_info_elem: Any, sig_val_b64: str, cert_bytes: bytes
) -> tuple[bool, str | None]:
    """Verify RSA-SHA256 signature over canonicalized SignedInfo."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    ET.register_namespace("ds", "http://www.w3.org/2000/09/xmldsig#")
    c14n_signed_info = ET.canonicalize(ET.tostring(signed_info_elem, encoding="utf-8")).encode(
        "utf-8"
    )

    try:
        sig_bytes = base64.b64decode(sig_val_b64.strip())
    except Exception:
        return False, "Invalid base64 in SignatureValue"

    try:
        cert = x509.load_pem_x509_certificate(cert_bytes)
        pub_key = cert.public_key()
        if not isinstance(pub_key, rsa.RSAPublicKey):
            return False, "Trust anchor must be an RSA public key"
        pub_key.verify(sig_bytes, c14n_signed_info, padding.PKCS1v15(), hashes.SHA256())
    except Exception as exc:
        return False, f"UIDAI digital signature verification failed: {exc}"

    return True, None


def _verify_with_builtin(raw_str: str, cert_bytes: bytes) -> tuple[bool, Any, str | None]:
    """Pure-Python XML-DSig verifier enforcing canonicalization and reference digest."""
    try:
        root = ET.fromstring(raw_str)
    except Exception as exc:
        return False, None, f"XML parse error: {exc}"

    (
        signed_info_elem,
        sig_val_elem,
        _,
        references,
        struct_err,
    ) = _parse_signature_structure(root)
    if struct_err:
        return False, None, struct_err

    uid_data_covered = False
    verified_uid_data = None

    for ref in references:
        valid_digest, target_node, dig_err = _verify_reference_digest(ref, root, raw_str)
        if not valid_digest or target_node is None:
            return False, None, dig_err

        if target_node.tag.endswith("UidData"):
            uid_data_covered = True
            verified_uid_data = target_node
        else:
            for elem in target_node.iter():
                if elem.tag.endswith("UidData"):
                    uid_data_covered = True
                    verified_uid_data = elem
                    break

    if not uid_data_covered or verified_uid_data is None:
        return (
            False,
            None,
            "Cryptographic verification failed: <UidData> is not covered by "
            "verified signature reference",
        )

    assert sig_val_elem is not None
    rsa_ok, rsa_err = _verify_signed_info_rsa(signed_info_elem, sig_val_elem.text or "", cert_bytes)
    if not rsa_ok:
        return False, None, rsa_err

    return True, root, None


def _verify_uidai_signature(  # noqa: C901
    root: Any,
    raw_str: str,
    active_cert_path: Path,
    now: datetime.datetime,
    errors: list[str],
    checks: list[AuthenticityCheck],
) -> tuple[bool, bool, Any]:
    """Verify certificate validity, XML-DSig reference digest, and digital signature."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes

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
        return False, False, None

    cert_valid = False
    sig_verified = False
    verified_node = None

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

        # 1. Signature wrapping defense: reject multiple Signature elements
        sig_elements = []
        if hasattr(root, "findall"):
            sig_elements = root.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
            if not sig_elements:
                sig_elements = [e for e in root.iter() if e.tag.endswith("Signature")]
        if len(sig_elements) == 0:
            errors.append("Signature block missing in offline artifact")
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=False,
                    level="A3",
                    detail="Missing SignatureValue in XML",
                )
            )
            return cert_valid, False, None
        if len(sig_elements) > 1:
            errors.append(
                "Security violation: multiple Signature elements detected "
                "(signature wrapping defense)"
            )
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=False,
                    level="A3",
                    detail="Multiple Signature elements rejected",
                )
            )
            return cert_valid, False, None

        # 2. Perform XML-DSig canonicalization, digest check, and signature verification
        has_signxml = False
        try:
            import signxml  # noqa: F401
            from lxml import etree  # noqa: F401

            has_signxml = True
        except ImportError:
            pass

        if has_signxml:
            sig_verified, verified_node, err_msg = _verify_with_signxml(raw_str, cert_bytes)
        else:
            sig_verified, verified_node, err_msg = _verify_with_builtin(raw_str, cert_bytes)

        if not sig_verified:
            if err_msg and err_msg not in errors:
                errors.append(err_msg)
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=False,
                    level="A3",
                    detail=err_msg or "Invalid RSA XML-DSig signature",
                )
            )
        else:
            checks.append(
                AuthenticityCheck(
                    name="uidai_digest_integrity",
                    passed=True,
                    level="A3",
                    detail="Cryptographic digest over <UidData> verified matching Reference",
                )
            )
            checks.append(
                AuthenticityCheck(
                    name="uidai_digital_signature",
                    passed=True,
                    level="A3",
                    detail="UIDAI RSA-2048 XML-DSig signature verified",
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
    return cert_valid, sig_verified, verified_node


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

            # Validated: entity expansion and DTDs explicitly rejected above
            root = StdET.fromstring(raw_str)  # nosec: B314 - entity expansion and DTDs checked above

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

    active_cert_path = Path(cert_path) if cert_path else DEFAULT_UIDAI_CERT
    cert_valid, sig_verified, verified_node = _verify_uidai_signature(
        root, raw_str, active_cert_path, now, errors, checks
    )

    is_valid = cert_valid and sig_verified and verified_node is not None and len(errors) == 0

    if is_valid:
        ref_id, masked_aadhaar, name, dob, gender, address = _extract_demographics(
            verified_node, root
        )
        last_4 = ref_id[:4] if len(ref_id) >= 4 else "XXXX"
        checks.append(
            AuthenticityCheck(
                name="dpdp_pii_boundary",
                passed=True,
                level="A1",
                detail=f"Identity masked to last 4 digits ({last_4}), raw Aadhaar not stored",
            )
        )
    else:
        ref_id, masked_aadhaar, name, dob, gender, address = "", "", "", "", "", {}
        checks.append(
            AuthenticityCheck(
                name="dpdp_pii_boundary",
                passed=True,
                level="A1",
                detail="Identity masked to last 4 digits (XXXX), raw Aadhaar not stored",
            )
        )

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
