import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any, cast

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.normalization import (
    normalize_aadhaar,
    normalize_cin,
    normalize_fssai,
    normalize_gstin,
    normalize_pan,
)
from mcp_india_stack.tools.aadhaar import validate_aadhaar as core_validate_aadhaar
from mcp_india_stack.tools.bulk_aadhaar import bulk_validate_aadhaar as core_bulk_validate_aadhaar
from mcp_india_stack.tools.cin import validate_cin as core_validate_cin
from mcp_india_stack.tools.driving_license import (
    validate_driving_license as core_validate_driving_license,
)
from mcp_india_stack.tools.fssai import validate_fssai as core_validate_fssai
from mcp_india_stack.tools.gstin import validate_gstin as core_validate_gstin
from mcp_india_stack.tools.llpin import validate_llpin as core_validate_llpin
from mcp_india_stack.tools.mobile import validate_mobile_number as core_validate_mobile_number
from mcp_india_stack.tools.pan import validate_pan as core_validate_pan
from mcp_india_stack.tools.pran import validate_pran as core_validate_pran
from mcp_india_stack.tools.tan import validate_tan as core_validate_tan
from mcp_india_stack.tools.upi import validate_upi_vpa as core_validate_upi_vpa
from mcp_india_stack.utils.responses import build_response


def _clamp_bulk_workers() -> int:
    """Parse MCP_INDIA_STACK_BULK_WORKERS with hard [1, 20] clamp."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 10
    return max(1, min(20, val))


_BULK_WORKERS = _clamp_bulk_workers()


def _validate_single_gstin(gstin: str) -> dict[str, Any]:
    """Validate a single GSTIN with error isolation."""
    try:
        return core_validate_gstin(gstin)
    except Exception as exc:
        return {
            "valid": False,
            "gstin": gstin,
            "errors": [f"Validation error: {exc}"],
            "warnings": [],
            "live_verified": False,
            "verification_source": "offline",
        }


def _validate_single_pan(pan: str) -> dict[str, Any]:
    """Validate a single PAN with error isolation."""
    from mcp_india_stack.tools import validate_pan as _validate_pan

    try:
        return _validate_pan(pan)
    except Exception as exc:
        return {"valid": False, "pan": pan, "errors": [f"Validation error: {exc}"], "warnings": []}


import re as _re

EPF_RE = _re.compile("^\\d{2}/\\d{5,6}/\\d{5,6}/\\d{3}$")
ESIC_RE = _re.compile("^[\\d]{2}-[\\d]+-[\\d]+$")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_gstin(
    gstin: Annotated[
        str,
        Field(
            min_length=1, max_length=30, description="15-character GSTIN (spaces/hyphens allowed)"
        ),
    ],
) -> dict[str, Any]:
    """Validate and decode an Indian GSTIN with checksum verification.

    Use when checking supplier/customer GSTINs before invoicing, reconciliation,
    or compliance workflows.

    Args:
            gstin: 15-character GSTIN (e.g., 27AAPFU0939F1ZV). Spaces/hyphens stripped.

    Returns:
            Standard envelope containing validity, state decode, embedded PAN,
            entity number, category, and checksum information.

    Notes:
            Validates structure and checksum only; does not verify active GSTN registration status.
    """
    normalized = normalize_gstin(gstin)["normalized_input"]
    try:
        result = core_validate_gstin(normalized)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"GSTIN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def bulk_validate_gstin(
    gstins: Annotated[list[str], Field(description="List of GSTINs to validate (max 500)")],
) -> dict[str, Any]:
    """Validate multiple GSTINs in parallel using ThreadPoolExecutor.

    Use when batch-validating vendor GSTINs for onboarding or reconciliation.
    Reduces N serial calls to ~N/10 parallel batches.

    Args:
            gstins: List of 15-character GSTIN strings.

    Returns:
            Standard envelope with per-GSTIN results, valid/invalid counts.

    Notes:
            Max 500 GSTINs per call. Configurable via MCP_INDIA_STACK_BULK_WORKERS.
            Individual validation errors don't fail the entire batch.
    """
    if not gstins:
        return build_response(
            success=False, data=None, errors=["Empty GSTIN list"], source="offline_algorithm"
        )
    if len(gstins) > 500:
        return build_response(
            success=False,
            data=None,
            errors=["Maximum 500 GSTINs per call"],
            source="offline_algorithm",
        )
    results: list[tuple[int, dict[str, Any]]] = []
    valid_count = 0
    invalid_count = 0
    with ThreadPoolExecutor(max_workers=_BULK_WORKERS) as executor:
        future_to_index: dict[Any, int] = {
            executor.submit(_validate_single_gstin, gstin): idx for idx, gstin in enumerate(gstins)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            result = future.result()
            results.append((idx, result))
            if result.get("valid"):
                valid_count += 1
            else:
                invalid_count += 1
    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]
    return build_response(
        success=True,
        data={
            "results": ordered_results,
            "total": len(gstins),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        },
        source="offline_algorithm",
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_pan(
    pan: Annotated[
        str, Field(min_length=1, max_length=20, description="10-char PAN (spaces/hyphens allowed)")
    ],
) -> dict[str, Any]:
    """Validate Indian PAN format and decode entity type from the 4th character.

    Use when normalizing tax identity records in KYC, invoicing, or vendor onboarding.

    Args:
            pan: PAN string, example: AAAPL1234C. Spaces and hyphens stripped automatically.

    Returns:
            Standard envelope containing format validity, entity type, and decoded segments.

    Notes:
            PAN check character is not publicly verifiable algorithmically.
    """
    normalized = normalize_pan(pan)["normalized_input"]
    try:
        result = core_validate_pan(normalized)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"PAN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def bulk_validate_pan(
    pans: Annotated[list[str], Field(description="List of PANs to validate (max 500)")],
) -> dict[str, Any]:
    """Validate multiple PANs in parallel."""
    if not pans:
        return build_response(success=False, data=None, errors=["Empty PAN list"])
    if len(pans) > 500:
        return build_response(success=False, data=None, errors=["Maximum 500 PANs per call"])
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []
    valid_count = 0
    with ThreadPoolExecutor(max_workers=_BULK_WORKERS) as executor:
        futures = {executor.submit(_validate_single_pan, pan): idx for idx, pan in enumerate(pans)}
        for future in as_completed(futures):
            result = future.result()
            results.append((futures[future], result))
            if result.get("valid"):
                valid_count += 1
    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]
    return build_response(
        success=True,
        data={"results": ordered_results, "total": len(pans), "valid_count": valid_count},
        source="offline_algorithm",
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_pan_type(pan: Annotated[str, Field(description="10-character PAN")]) -> dict[str, Any]:
    """Decode PAN entity type from 4th character."""
    from mcp_india_stack.tools.pan import validate_pan

    result = validate_pan(pan)
    if result.get("success"):
        entity_code = result.get("data", {}).get("entity_code", "")
        entity_types = {
            "P": ("Individual", "NRI requires Form 60/61"),
            "C": ("Company", "Requires DIN for directors"),
            "H": ("Hindu Undivided Family (HUF)", "HUF"),
            "F": ("Firm", "Partnership/LLP"),
            "A": ("Association of Persons (AOP)", "AOP"),
            "B": ("Body of Individuals (BOI)", "BOI"),
            "G": ("Government", "Central/State"),
            "J": ("Artificial Juridical Person", "AJP"),
            "L": ("Local Authority", "Panchayat/Municipal"),
            "T": ("Trust", "Trust"),
            "E": ("Limited Liability Partnership (LLP)", "LLP"),
        }
        entity_label, kyc_hint = entity_types.get(entity_code, ("Unknown", ""))
        return build_response(
            success=True,
            data={
                "pan": pan.upper(),
                "entity_type_code": entity_code,
                "entity_type_label": entity_label,
                "kyc_routing_hint": kyc_hint,
                "normalized_input": pan.upper().strip(),
            },
            validated_by=["format", "checksum"],
            source="offline_algorithm",
        )
    return build_response(
        success=False, data=result, errors=result.get("errors", []), source="offline_algorithm"
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_upi_vpa(
    vpa: Annotated[
        str, Field(min_length=3, max_length=300, description="UPI VPA, example: user@okaxis")
    ],
) -> dict[str, Any]:
    """Validate UPI VPA structure and decode known provider handles.

    Use when checking whether a UPI address is structurally valid before payment routing.

    Args:
            vpa: UPI virtual payment address in username@handle format.

    Returns:
            Standard envelope containing normalized VPA, known_provider flag, and provider metadata.

    Notes:
            Unknown handles are not auto-invalidated because NPCI handle lists evolve over time.
    """
    try:
        result = core_validate_upi_vpa(vpa)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"UPI validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_aadhaar(
    aadhaar: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="12-digit Aadhaar number. Spaces and hyphens accepted. Example: 2959 4583 7261",  # noqa: E501
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian Aadhaar number with Verhoeff checksum verification.

    Use when checking Aadhaar format and checksum in KYC, identity verification,
    or government benefit workflows.

    Args:
            aadhaar: 12-digit Aadhaar number. Spaces and hyphens are stripped.

    Returns:
            Standard envelope containing validity, checksum result, formatted display,
            and first-digit check.

    Notes:
            Validates format and Verhoeff checksum only. Not connected to UIDAI.
    """
    normalized = normalize_aadhaar(aadhaar)["normalized_input"]
    try:
        result = core_validate_aadhaar(normalized)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Aadhaar validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def bulk_validate_aadhaar(
    numbers: Annotated[
        list[str], Field(description="List of Aadhaar numbers to validate (max 500)")
    ],
) -> dict[str, Any]:
    """Validate multiple Aadhaar numbers in parallel using ThreadPoolExecutor.

    Use when batch-validating Aadhaar numbers for KYC, onboarding, or
    compliance workflows.

    Args:
        numbers: List of Aadhaar numbers (with or without spaces/hyphens).

    Returns:
        Standard envelope with per-Aadhaar results and valid/invalid counts.

    Notes:
        Max 500 Aadhaars per call. Uses same Verhoeff validation as single tool.
    """
    try:
        result = core_bulk_validate_aadhaar(numbers=numbers)
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Bulk Aadhaar validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_voter_id(
    voter_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="10-character EPIC number (spaces/hyphens allowed). Example: ABC1234567",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian Voter ID (EPIC) number format.

    Use when verifying voter ID format in KYC, identity, or electoral workflows.

    Args:
            voter_id: EPIC number (3 letters + 7 digits). Spaces/hyphens stripped.

    Returns:
            Standard envelope containing validity, prefix, serial, and format type.

    Notes:
            Format validation only. Detects possible legacy EPIC formats.
    """
    from mcp_india_stack.tools.voter_id import validate_voter_id as core_validate_voter_id

    cleaned = str(voter_id).strip().upper().replace(" ", "").replace("-", "")
    try:
        result = core_validate_voter_id(cleaned)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Voter ID validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_driving_license(
    dl_number: Annotated[
        str,
        Field(
            min_length=1,
            max_length=25,
            description="Indian DL number, 15 chars (spaces/hyphens allowed). Ex: MH0220191234567",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian driving license number format and decode segments.

    Use when verifying DL format, extracting state/RTO/year in KYC workflows.

    Args:
            dl_number: Driving license number. Hyphens/spaces stripped automatically.

    Returns:
            Standard envelope containing validity, state code, state name, RTO code,
            year of issue, and serial number.

    Notes:
            Format validation only. Handles non-standard pre-Sarathi formats gracefully.
    """
    try:
        result = core_validate_driving_license(dl_number)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"DL validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_passport(
    passport_number: Annotated[
        str,
        Field(
            min_length=1,
            max_length=15,
            description="8-char Indian passport (spaces/hyphens allowed). Ex: A1234567",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian passport number format.

    Use when verifying passport format in KYC, travel, or identity workflows.

    Args:
            passport_number: 1 letter + 7 digits. Spaces and hyphens stripped automatically.

    Returns:
            Standard envelope containing validity, series letter, and serial number.

    Notes:
            Format validation only. No public checksum algorithm exists.
    """
    from mcp_india_stack.tools.passport import validate_passport as core_validate_passport

    cleaned = str(passport_number).strip().upper().replace(" ", "").replace("-", "")
    try:
        result = core_validate_passport(cleaned)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Passport validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_cin(
    cin: Annotated[
        str,
        Field(
            min_length=1,
            max_length=30,
            description="21-character CIN (spaces/hyphens allowed). Example: L17110MH1973PLC019786",
        ),
    ],
) -> dict[str, Any]:
    """Validate and decode an Indian CIN (Company Identification Number).

    Use when verifying company registration data, extracting listing status,
    NIC code, state, year, and company type from a CIN.

    Args:
            cin: 21-character CIN string. Spaces and hyphens stripped automatically.

    Returns:
            Standard envelope containing decoded fields: listing status, NIC code,
            state, year of incorporation, company type, and serial number.

    Notes:
            Format validation with field decoding. No public checksum.
    """
    normalized = normalize_cin(cin)["normalized_input"]
    try:
        result = core_validate_cin(normalized)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"CIN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_din(
    din: Annotated[
        str,
        Field(
            min_length=1,
            max_length=15,
            description="8-digit DIN (spaces allowed). Example: 00012345",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian DIN (Director Identification Number) format.

    Use when verifying director identity numbers in MCA compliance workflows.

    Args:
            din: 8-digit numeric DIN string. Shorter inputs zero-padded. Spaces stripped.

    Returns:
            Standard envelope containing validity and normalized DIN.

    Notes:
            Format validation only. Cannot verify director status with MCA.
    """
    from mcp_india_stack.tools.din import validate_din as core_validate_din

    cleaned = str(din).strip().replace(" ", "")
    try:
        result = core_validate_din(cleaned)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=cast(list[str], result.get("errors", [])),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"DIN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_fssai(
    license_number: Annotated[
        str,
        Field(
            min_length=1,
            max_length=25,
            description="14-digit FSSAI license (spaces/hyphens allowed). Ex: 10019000000001",
        ),
    ],
) -> dict[str, Any]:
    """Validate FSSAI (Food Safety) license number format and decode details.

    Use when verifying food business operator licenses in compliance checks.

    Args:
            license_number: 14-digit FSSAI license. Spaces/hyphens stripped.

    Returns:
            Standard envelope with validation, state, license type, year decoded.

    Notes:
            The 14-digit format encodes: state(2) + year(2) + type(1) + sequence(9).
            Type: 1=Central, 2=State, 3=State (turnover-based).
    """
    normalized = normalize_fssai(license_number)["normalized_input"]
    try:
        result = core_validate_fssai(normalized)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            normalized_input=result.get("normalized_input"),
            validated_by=["format"] if result.get("valid") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"FSSAI validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_tan(
    tan: Annotated[str, Field(description="10-character TAN (e.g., ABCD12345E)")],
) -> dict[str, Any]:
    """Validate TAN (Tax Deduction Account Number) format.

    Use when verifying TAN format for TDS compliance.

    Args:
        tan: 10-character TAN

    Returns:
        Validation result with decoded segments.
    """
    try:
        result = core_validate_tan(tan)
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"TAN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_mobile_number(
    mobile: Annotated[str, Field(description="10-digit mobile number with or without +91/0")],
) -> dict[str, Any]:
    """Validate Indian mobile number and detect operator/circle.

    Use when validating mobile numbers for KYC or contact verification.

    Args:
        mobile: Mobile number with or without +91/0

    Returns:
        Validation result with operator and telecom circle.
    """
    try:
        result = core_validate_mobile_number(mobile)
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Mobile validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_pran(pran: Annotated[str, Field(description="12-digit PRAN")]) -> dict[str, Any]:
    """Validate PRAN (Permanent Retirement Account Number) for NPS.

    Use when verifying NPS account numbers.

    Args:
        pran: 12-digit PRAN

    Returns:
        Validation result with subscriber category.
    """
    try:
        result = core_validate_pran(pran)
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"PRAN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_llpin(
    llpin: Annotated[str, Field(description="LLPIN in format AAA-XXXX or AAAXXXX")],
) -> dict[str, Any]:
    """Validate LLPIN (Limited Liability Partnership Identification Number).

    Use when verifying LLP registration numbers.

    Args:
        llpin: LLPIN in format AAA-XXXX

    Returns:
        Validation result with decoded segments.
    """
    try:
        result = core_validate_llpin(llpin)
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"LLPIN validation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_epf_code(
    code: Annotated[str, Field(description="EPF establishment code (XX/XXXXX/XXXXXX/XXX)")],
) -> dict[str, Any]:
    """Validate EPF establishment code."""
    normalized = code.strip().upper().replace(" ", "")
    if not EPF_RE.match(normalized):
        return build_response(
            success=False,
            data={"code": code, "normalized_input": normalized},
            errors=["Invalid EPF format. Expected: XX/XXXXX/XXXXXX/XXX"],
            source="offline_algorithm",
        )
    parts = normalized.split("/")
    return build_response(
        success=True,
        data={
            "code": code,
            "normalized_input": normalized,
            "region_code": parts[0],
            "office_code": parts[1],
            "establishment_code": parts[2],
            "extension": parts[3],
        },
        validated_by=["format"],
        source="offline_algorithm",
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_esic_code(
    code: Annotated[str, Field(description="ESIC employer code (XX-XXXXX-XXXXX)")],
) -> dict[str, Any]:
    """Validate ESIC employer code."""
    normalized = code.strip().upper().replace(" ", "")
    if not ESIC_RE.match(normalized):
        return build_response(
            success=False,
            data={"code": code, "normalized_input": normalized},
            errors=["Invalid ESIC format. Expected: XX-XXXXX-XXXXX"],
            source="offline_algorithm",
        )
    parts = normalized.split("-")
    return build_response(
        success=True,
        data={
            "code": code,
            "normalized_input": normalized,
            "regional_code": parts[0],
            "employer_code": parts[1],
            "sub_code": parts[2],
        },
        validated_by=["format"],
        source="offline_algorithm",
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_digilocker_uri(
    uri: Annotated[str, Field(description="DigiLocker document URI")],
) -> dict[str, Any]:
    """Decode DigiLocker document URI and map to validator."""
    errors = []
    warnings = []
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
    expected_fields = []
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


@mcp.resource("india://schema/validate_gstin")
def schema_validate_gstin() -> dict[str, Any]:
    """JSON schema for validate_gstin output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "gstin": {"type": "string"},
            "state_code": {"type": "string"},
            "state_name": {"type": "string"},
            "pan": {"type": "string"},
            "entity_number": {"type": "string"},
            "checksum_valid": {"type": "boolean"},
            "expected_checksum": {"type": "string"},
            "category": {"type": "string"},
            "format_validity": {"type": "string"},
            "live_verified": {"type": "boolean"},
            "verification_source": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_pan")
def schema_validate_pan() -> dict[str, Any]:
    """JSON schema for validate_pan output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "pan": {"type": "string"},
            "entity_type": {"type": "string"},
            "first_char": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_upi_vpa")
def schema_validate_upi_vpa() -> dict[str, Any]:
    """JSON schema for validate_upi_vpa output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "normalized_vpa": {"type": "string"},
            "known_provider": {"type": "boolean"},
            "provider": {"type": "string"},
            "handle": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_aadhaar")
def schema_validate_aadhaar() -> dict[str, Any]:
    """JSON schema for validate_aadhaar output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "aadhaar": {"type": "string"},
            "checksum_valid": {"type": "boolean"},
            "formatted": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_voter_id")
def schema_validate_voter_id() -> dict[str, Any]:
    """JSON schema for validate_voter_id output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "voter_id": {"type": "string"},
            "prefix": {"type": "string"},
            "serial": {"type": "string"},
            "format_type": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_driving_license")
def schema_validate_driving_license() -> dict[str, Any]:
    """JSON schema for validate_driving_license output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "dl_number": {"type": "string"},
            "state_code": {"type": "string"},
            "state_name": {"type": "string"},
            "rto_code": {"type": "string"},
            "year_of_issue": {"type": "string"},
            "serial": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_passport")
def schema_validate_passport() -> dict[str, Any]:
    """JSON schema for validate_passport output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "passport_number": {"type": "string"},
            "series": {"type": "string"},
            "serial": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_cin")
def schema_validate_cin() -> dict[str, Any]:
    """JSON schema for validate_cin output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "cin": {"type": "string"},
            "listing_status": {"type": "string"},
            "nic_code": {"type": "string"},
            "state": {"type": "string"},
            "year_of_incorporation": {"type": "string"},
            "company_type": {"type": "string"},
            "serial_number": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/validate_din")
def schema_validate_din() -> dict[str, Any]:
    """JSON schema for validate_din output."""
    return {
        "type": "object",
        "properties": {
            "valid": {"type": "boolean"},
            "din": {"type": "string"},
            "normalized_din": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/bulk_validate_gstin")
def schema_bulk_validate_gstin() -> dict[str, Any]:
    """JSON schema for bulk_validate_gstin output."""
    return {
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "total": {"type": "integer"},
            "valid_count": {"type": "integer"},
            "invalid_count": {"type": "integer"},
        },
    }
