"""DigiLocker URI decoder and validator routing."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.utils.responses import build_response


def decode_digilocker_uri(uri: str) -> dict[str, Any]:
    """Decode DigiLocker document URI and map to validator.

    Args:
        uri: DigiLocker document URI (e.g., dlg://uidai/aadhaar).

    Returns:
        Standard envelope with parsed URI components, document type, and validator routing.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not uri.startswith("dlg://"):
        errors.append("Invalid DigiLocker URI format. Must start with 'dlg://'")
        return build_response(success=False, data=None, errors=errors, source="offline_algorithm")

    path = uri.replace("dlg://", "")
    parts = path.split("/")

    if len(parts) < 2:
        errors.append("Invalid DigiLocker URI format")
        return build_response(success=False, data=None, errors=errors, source="offline_algorithm")

    issuer = parts[0].lower()
    doc_type = parts[1].lower() if len(parts) > 1 else ""

    validators = {
        ("uidai", "aadhaar"): ("validate_aadhaar", "Aadhaar Card", ["aadhaar_number"]),
        ("mha", "passport"): ("validate_passport", "Passport", ["passport_number"]),
        ("parivahan", "dl", "driving_license"): (
            "validate_driving_license",
            "Driving License",
            ["dl_number"],
        ),
        ("epic", "voter"): ("validate_voter_id", "Voter ID", ["epic_number"]),
        ("incometax", "pan"): ("validate_pan", "PAN Card", ["pan"]),
    }

    verification_pairing = None
    document_type = "Unknown"
    expected_fields: list[str] = []

    for key, (validator, doc_type_label, fields) in validators.items():
        if any(k in issuer or k in doc_type for k in key):
            verification_pairing = validator
            document_type = doc_type_label
            expected_fields = fields
            break

    if not verification_pairing:
        warnings.append(f"Unknown issuer: {issuer}. Manual verification recommended.")
        document_type = f"Document from {issuer}"
        expected_fields = ["document_id"]

    return build_response(
        success=True,
        data={
            "uri": uri,
            "issuer": issuer,
            "document_type": document_type,
            "expected_fields": expected_fields,
            "verification_pairing": verification_pairing,
            "normalized_input": uri.strip(),
        },
        validated_by=["format"],
        source="offline_algorithm",
    )
