"""FastMCP server for mcp-india-stack."""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any, cast

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.tools import (
    calculate_advance_tax as core_calculate_advance_tax,
)
from mcp_india_stack.tools import (
    calculate_capital_gains as core_calculate_capital_gains,
)
from mcp_india_stack.tools import (
    calculate_gst as core_calculate_gst,
)
from mcp_india_stack.tools import (
    calculate_hra_exemption as core_calculate_hra,
)
from mcp_india_stack.tools import (
    calculate_income_tax as core_calculate_income_tax,
)
from mcp_india_stack.tools import (
    calculate_surcharge as core_calculate_surcharge,
)
from mcp_india_stack.tools import (
    calculate_tds as core_calculate_tds,
)
from mcp_india_stack.tools import (
    decode_state_code as core_decode_state_code,
)
from mcp_india_stack.tools import (
    lookup_bbps_biller as core_lookup_bbps_biller,
)
from mcp_india_stack.tools import (
    lookup_hsn_code as core_lookup_hsn_code,
)
from mcp_india_stack.tools import (
    lookup_ifsc as core_lookup_ifsc,
)
from mcp_india_stack.tools import (
    lookup_pincode as core_lookup_pincode,
)
from mcp_india_stack.tools import (
    validate_aadhaar as core_validate_aadhaar,
)
from mcp_india_stack.tools import (
    validate_cin as core_validate_cin,
)
from mcp_india_stack.tools import (
    validate_driving_license as core_validate_driving_license,
)
from mcp_india_stack.tools import (
    validate_fssai as core_validate_fssai,
)
from mcp_india_stack.tools import (
    validate_gstin as core_validate_gstin,
)
from mcp_india_stack.tools import (
    validate_pan as core_validate_pan,
)
from mcp_india_stack.tools import (
    validate_upi_vpa as core_validate_upi_vpa,
)
from mcp_india_stack.utils.responses import build_response

mcp = FastMCP(
    name="mcp-india-stack",
    instructions=(
        "Indian financial and government data tools for AI agents. Provides offline "
        "validation for GSTIN, IFSC, PAN, UPI VPA, Aadhaar, Voter ID, DL, Passport, "
        "CIN, DIN; tax calculators for income tax, TDS, GST, surcharge; and lookups "
        "for pincodes, HSN/SAC codes, and state codes. Zero authentication required."
    ),
)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def lookup_ifsc(
    ifsc_code: Annotated[
        str,
        Field(
            min_length=1,
            max_length=32,
            description="IFSC code, expected 11 chars. Example: HDFC0000001",
        ),
    ],
) -> dict[str, Any]:
    """Look up an Indian IFSC code from bundled dataset with live fallback support.

    Use this when you need bank branch details from an IFSC code in invoices,
    onboarding forms, or payment validation workflows.

    Args:
            ifsc_code: IFSC string to validate and lookup. Case-insensitive; whitespace is trimmed.

    Returns:
            Standard envelope containing found flag, branch details, payment rails, and source.

    Notes:
            If not found locally, attempts live lookup at ifsc.razorpay.com with 3s timeout.
    """
    try:
        result = core_lookup_ifsc(ifsc_code)
        return build_response(
            success=bool(result.get("found")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source=result.get("source", "bundled_dataset"),
        )
    except Exception as exc:
        return build_response(
            success=False,
            data=None,
            errors=[
                f"IFSC lookup failed: {exc}",
                "This may indicate dataset corruption. Reinstall mcp-india-stack.",
            ],
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
    from mcp_india_stack.normalization import normalize_gstin

    normalized = normalize_gstin(gstin)["normalized_input"]
    try:
        result = core_validate_gstin(normalized)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
            normalized_input=result.get("normalized_input", normalized)
            if result.get("valid")
            else None,
            validated_by=["format", "checksum"] if result.get("valid") else [],
            confidence=0.65 if result.get("valid") else 0.0,
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"GSTIN validation failed: {exc}"],
            source="offline_algorithm",
        )


_BULK_WORKERS = int(os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10"))


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


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def bulk_validate_gstin(
    gstins: Annotated[
        list[str],
        Field(description="List of GSTINs to validate (max 500)"),
    ],
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
            success=False,
            data=None,
            errors=["Empty GSTIN list"],
            source="offline_algorithm",
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


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
    from mcp_india_stack.normalization import normalize_pan

    normalized = normalize_pan(pan)["normalized_input"]
    try:
        result = core_validate_pan(normalized)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"PAN validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_upi_vpa(
    vpa: Annotated[
        str,
        Field(min_length=3, max_length=300, description="UPI VPA, example: user@okaxis"),
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
            success=False,
            errors=[f"UPI validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def lookup_pincode(
    pincode: Annotated[str, Field(min_length=1, max_length=16, description="6-digit pincode")],
) -> dict[str, Any]:
    """Look up India pincode details and return all post offices for that code.

    Use for address normalization, district/state extraction, and GST state crosswalk use-cases.

    Args:
            pincode: 6-digit pincode; spaces/hyphens are accepted and normalized.

    Returns:
            Standard envelope with location hierarchy and post_offices array.

    Notes:
            One pincode may map to multiple post offices and all are returned.
    """
    try:
        result = core_lookup_pincode(pincode)
        return build_response(
            success=bool(result.get("found")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="bundled_dataset",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Pincode lookup failed: {exc}"],
            source="bundled_dataset",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def lookup_hsn_code(
    code: Annotated[
        str | None,
        Field(default=None, description="HSN/SAC code (2-8 digits) for exact lookup"),
    ] = None,
    keyword: Annotated[
        str | None,
        Field(default=None, description="Keyword for description search, example: coffee"),
    ] = None,
) -> dict[str, Any]:
    """Lookup HSN/SAC by exact code or search by keyword in code descriptions.

    Use for GST classification workflows where users provide a code or only a product keyword.

    Args:
            code: Optional exact HSN/SAC code (2, 4, 6, or 8 digits).
            keyword: Optional plain-text search token over description field.

    Returns:
            Standard envelope with exact match data or top 5 keyword matches.

    Notes:
            Returns static master data; GST applicability can vary by conditions.
    """
    try:
        result = core_lookup_hsn_code(code=code, keyword=keyword)
        return build_response(
            success=bool(result.get("found")),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="bundled_dataset",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"HSN lookup failed: {exc}"],
            source="bundled_dataset",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def decode_state_code(
    value: Annotated[
        str,
        Field(min_length=2, max_length=15, description="2-digit state code or GSTIN"),
    ],
) -> dict[str, Any]:
    """Decode Indian GST state code metadata from a code or GSTIN prefix.

    Use when you need canonical state name, abbreviation, capital, and GST zone mapping.

    Args:
            value: Two-digit code like 27 or GSTIN like 27AAPFU0939F1ZV.

    Returns:
            Standard envelope containing decoded state metadata.
    """
    try:
        result = core_decode_state_code(value)
        return build_response(
            success=bool(result.get("found")),
            data=result,
            errors=[str(result["error"])] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"State code decode failed: {exc}"],
            source="offline_algorithm",
        )


# ---------------------------------------------------------------------------
# v0.2.0 — Validation tools
# ---------------------------------------------------------------------------


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_aadhaar(
    aadhaar: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description=(
                "12-digit Aadhaar number. Spaces and hyphens accepted. Example: 2959 4583 7261"
            ),
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
    from mcp_india_stack.normalization import normalize_aadhaar

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
            success=False,
            errors=[f"Aadhaar validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
            success=False,
            errors=[f"Voter ID validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
            success=False,
            errors=[f"DL validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
            success=False,
            errors=[f"Passport validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
    from mcp_india_stack.normalization import normalize_cin

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
            success=False,
            errors=[f"CIN validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
            success=False,
            errors=[f"DIN validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
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
    from mcp_india_stack.normalization import normalize_fssai

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
            success=False,
            errors=[f"FSSAI validation failed: {exc}"],
            source="offline_algorithm",
        )


# ---------------------------------------------------------------------------
# v0.2.0 — Tax calculation tools
# ---------------------------------------------------------------------------


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_income_tax(
    gross_income: Annotated[
        float,
        Field(description="Annual gross income in rupees. Example: 1500000"),
    ],
    regime: Annotated[
        str,
        Field(description="Tax regime: 'new', 'old', or 'both' for comparison"),
    ] = "both",
    taxpayer_type: Annotated[
        str,
        Field(description="'individual', 'senior_citizen', or 'super_senior_citizen'"),
    ] = "individual",
    deduction_80c: Annotated[
        float,
        Field(description="Section 80C deduction (PF, ELSS, LIC), capped at 1.5L"),
    ] = 0,
    deduction_80d_self: Annotated[
        float,
        Field(description="Section 80D medical insurance self, capped at 25K"),
    ] = 0,
    deduction_80d_parents: Annotated[
        float,
        Field(description="Section 80D medical insurance parents, capped at 25K/50K"),
    ] = 0,
    deduction_80d_senior_parents: Annotated[
        bool,
        Field(description="If True, parents 80D cap is 50K instead of 25K"),
    ] = False,
    deduction_80ccd_nps: Annotated[
        float,
        Field(description="Additional NPS deduction under 80CCD(1B), capped at 50K"),
    ] = 0,
    deduction_24b: Annotated[
        float,
        Field(description="Home loan interest under Section 24(b), capped at 2L"),
    ] = 0,
    other_deductions: Annotated[
        float,
        Field(description="Other deductions (no cap)"),
    ] = 0,
) -> dict[str, Any]:
    """Calculate Indian income tax for FY2025-26 under old, new, or both regimes.

    Use when computing tax liability, comparing regimes, or planning deductions.
    Includes slab computation, Section 87A rebate, surcharge with marginal relief,
    and health & education cess.

    Args:
            gross_income: Annual gross income in rupees.
            regime: 'new', 'old', or 'both' for side-by-side comparison.
            taxpayer_type: Category for slab selection.
            deduction_80c: Old regime only — Section 80C amount.
            deduction_80d_self: Old regime only — medical insurance self.
            deduction_80d_parents: Old regime only — medical insurance parents.
            deduction_80d_senior_parents: Old regime only — senior parent flag.
            deduction_80ccd_nps: Old regime only — NPS additional.
            deduction_24b: Old regime only — home loan interest.
            other_deductions: Old regime only — other amounts.

    Returns:
            Standard envelope with per-regime breakdown, effective rate, monthly tax,
            take-home, and regime recommendation when both requested.

    Notes:
            FY2025-26 rates. Estimate only — consult a CA for filing.
    """
    try:
        result = core_calculate_income_tax(
            gross_income=gross_income,
            regime=regime,
            taxpayer_type=taxpayer_type,
            deduction_80c=deduction_80c,
            deduction_80d_self=deduction_80d_self,
            deduction_80d_parents=deduction_80d_parents,
            deduction_80d_senior_parents=deduction_80d_senior_parents,
            deduction_80ccd_nps=deduction_80ccd_nps,
            deduction_24b=deduction_24b,
            other_deductions=other_deductions,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Income tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_tds(
    section: Annotated[
        str,
        Field(description="TDS section key, e.g. '194C_individual', '194J_professional'"),
    ],
    payment_amount: Annotated[
        float,
        Field(description="Gross payment amount in rupees"),
    ],
    pan_available: Annotated[
        bool,
        Field(description="Whether payee has provided PAN"),
    ],
    is_senior_citizen: Annotated[
        bool,
        Field(description="For 194A bank interest — applies higher threshold for seniors"),
    ] = False,
) -> dict[str, Any]:
    """Calculate TDS for a given section and payment amount (FY2025-26).

    Use when computing withholding tax on contractor payments, professional fees,
    interest, rent, commissions, or purchase of goods.

    Args:
            section: TDS section key from supported sections.
            payment_amount: Gross payment in rupees.
            pan_available: Whether payee PAN is available (affects rate).
            is_senior_citizen: For 194A bank interest threshold.

    Returns:
            Standard envelope with TDS applicability, rate, amount, net payment.

    Notes:
            FY2025-26 rates. Actual rates may vary by DTAA or Form 15G/15H.
    """
    try:
        result = core_calculate_tds(
            section=section,
            payment_amount=payment_amount,
            pan_available=pan_available,
            is_senior_citizen=is_senior_citizen,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"TDS calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_gst(
    amount: Annotated[
        float,
        Field(description="Base amount in rupees (or inclusive amount if flagged)"),
    ],
    gst_rate: Annotated[
        float,
        Field(description="GST rate as percentage: 0, 0.1, 0.25, 1.5, 3, 5, 12, 18, 28"),
    ],
    transaction_type: Annotated[
        str,
        Field(description="'intra_state' (CGST+SGST) or 'inter_state' (IGST)"),
    ],
    amount_includes_gst: Annotated[
        bool,
        Field(description="If True, back-calculate base from GST-inclusive amount"),
    ] = False,
    cess_category: Annotated[
        str,
        Field(description="Cess category for 28% items. Default: 'default' (no cess)"),
    ] = "default",
) -> dict[str, Any]:
    """Calculate GST breakdown with CGST/SGST/IGST split and optional cess.

    Use when computing tax for invoices, quotations, or GST compliance.

    Args:
            amount: Base amount or GST-inclusive amount in rupees.
            gst_rate: Valid GST rate percentage.
            transaction_type: 'intra_state' or 'inter_state'.
            amount_includes_gst: Set True to back-calculate base.
            cess_category: For 28% items, specify applicable cess.

    Returns:
            Standard envelope with base amount, CGST/SGST/IGST breakdown,
            cess amount, total GST, and total payable amount.

    Notes:
            Rates are for general reference. Actual classification may vary.
    """
    try:
        result = core_calculate_gst(
            amount=amount,
            gst_rate=gst_rate,
            transaction_type=transaction_type,
            amount_includes_gst=amount_includes_gst,
            cess_category=cess_category,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"GST calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_surcharge(
    total_income: Annotated[
        float,
        Field(description="Total income in rupees"),
    ],
    base_tax: Annotated[
        float,
        Field(description="Base tax amount before surcharge"),
    ],
    regime: Annotated[
        str,
        Field(description="'new' or 'old' tax regime"),
    ],
) -> dict[str, Any]:
    """Calculate surcharge and marginal relief for a given income and base tax.

    Use when computing surcharge as a standalone calculation, separate from
    the full income tax tool. The income tax tool uses this logic internally.

    Args:
            total_income: Total income in rupees.
            base_tax: Base tax amount before surcharge.
            regime: 'new' (capped at 25%) or 'old' (up to 37%).

    Returns:
            Standard envelope with surcharge rate, before/after marginal relief,
            and cess base.

    Notes:
            FY2025-26 rates. New regime surcharge capped at 25%.
    """
    try:
        result = core_calculate_surcharge(
            total_income=total_income,
            base_tax=base_tax,
            regime=regime,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Surcharge calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_hra_exemption(
    basic_salary: Annotated[
        float,
        Field(description="Monthly basic salary in rupees"),
    ],
    hra_received: Annotated[
        float,
        Field(description="Annual HRA received from employer in rupees"),
    ],
    rent_paid: Annotated[
        float,
        Field(description="Annual rent paid in rupees"),
    ],
    city_type: Annotated[
        str,
        Field(description="'metro' (Delhi/Mumbai/Chennai/Kolkata) or 'non_metro'"),
    ] = "non_metro",
    is_government_employee: Annotated[
        bool,
        Field(description="True for government employees using simplified formula"),
    ] = False,
) -> dict[str, Any]:
    """Calculate House Rent Allowance (HRA) exemption under Section 10(13A).

    Use when computing tax-exempt HRA component for salary structuring or
    income tax filing. Compares three conditions and takes minimum.

    Args:
            basic_salary: Monthly basic salary.
            hra_received: Annual HRA received from employer.
            rent_paid: Annual rent paid.
            city_type: 'metro' (50% of salary) or 'non_metro' (40% of salary).
            is_government_employee: Use simplified formula for government employees.

    Returns:
            Standard envelope with exemption amount, taxable HRA, and breakdown.

    Notes:
            The actual exemption is the minimum of:
            1. HRA received
            2. Rent paid minus 10% of salary
            3. 50% of salary (metro) or 40% (non_metro)
    """
    try:
        result = core_calculate_hra(
            basic_salary=basic_salary,
            hra_received=hra_received,
            rent_paid=rent_paid,
            city_type=city_type,
            is_government_employee=is_government_employee,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"HRA calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_capital_gains(
    sale_price: Annotated[
        float,
        Field(description="Sale proceeds in rupees"),
    ],
    purchase_price: Annotated[
        float,
        Field(description="Original purchase price in rupees"),
    ],
    asset_type: Annotated[
        str,
        Field(
            description="Asset type: equity, mutual_fund, real_estate, gold, debentures, crypto",
        ),
    ] = "equity",
    holding_period_days: Annotated[
        int,
        Field(description="Number of days held before sale"),
    ] = 365,
    inflation_index_purchase: Annotated[
        float | None,
        Field(description="CII for purchase year (for indexation)"),
    ] = None,
    inflation_index_sale: Annotated[
        float | None,
        Field(description="CII for sale year (for indexation)"),
    ] = None,
    expenses_on_sale: Annotated[
        float,
        Field(description="Brokerage, registration and other expenses on sale"),
    ] = 0,
    improvements: Annotated[
        float,
        Field(description="Cost of improvements (for real estate)"),
    ] = 0,
) -> dict[str, Any]:
    """Calculate capital gains tax for various asset types (FY2025-26).

    Use when computing tax liability on sale of equity, mutual funds,
    real estate, gold, or other capital assets.

    Args:
            sale_price: Sale proceeds after expenses.
            purchase_price: Original purchase price.
            asset_type: Type of asset sold.
            holding_period_days: Days held before sale.
            inflation_index_purchase: Cost Inflation Index for purchase year.
            inflation_index_sale: Cost Inflation Index for sale year.
            expenses_on_sale: Expenses incurred during sale.
            improvements: Cost of improvements (for real estate).

    Returns:
            Standard envelope with STCG/LTCG breakdown, tax rates, and liability.

    Notes:
            Budget 2024 rates: STCG 20% (equity/MF), LTCG 12.5% (equity/MF threshold 100K).
            Real estate without indexation taxed at 20%.
    """
    try:
        result = core_calculate_capital_gains(
            sale_price=sale_price,
            purchase_price=purchase_price,
            asset_type=asset_type,
            holding_period_days=holding_period_days,
            inflation_index_purchase=inflation_index_purchase,
            inflation_index_sale=inflation_index_sale,
            expenses_on_sale=expenses_on_sale,
            improvements=improvements,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Capital gains calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_advance_tax(
    estimated_income: Annotated[
        float,
        Field(description="Estimated total income for FY in rupees"),
    ],
    regime: Annotated[
        str,
        Field(description="'new' or 'old' tax regime"),
    ] = "new",
    taxpayer_type: Annotated[
        str,
        Field(description="'individual', 'senior_citizen', or 'super_senior_citizen'"),
    ] = "individual",
    existing_tds: Annotated[
        float,
        Field(description="TDS already deducted or to be deducted in rupees"),
    ] = 0,
) -> dict[str, Any]:
    """Calculate quarterly advance tax installment schedule per Sections 234B and 234C.

    Use when planning quarterly tax payments to avoid interest penalties.
    Provides due dates and amounts for each installment.

    Args:
            estimated_income: Estimated annual income for FY2025-26.
            regime: Tax regime for calculation.
            taxpayer_type: Category for slab selection.
            existing_tds: TDS already likely to be deducted.

    Returns:
            Standard envelope with quarterly breakdown and interest rules.

    Notes:
            Due dates: June 15 (15%), Sept 15 (45%), Dec 15 (75%), Mar 15 (100%).
            Interest 1% per month for delay under Section 234C.
    """
    try:
        result = core_calculate_advance_tax(
            estimated_income=estimated_income,
            regime=regime,
            taxpayer_type=taxpayer_type,
            existing_tds=existing_tds,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Advance tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def lookup_bbps_biller(
    category: Annotated[
        str | None,
        Field(
            description="electricity, gas, dth, water, broadband, fastag, insurance, mobile",
        ),
    ] = None,
    state: Annotated[
        str | None,
        Field(description="State name (e.g., 'Maharashtra', 'Delhi') or 'all'"),
    ] = None,
    biller_id: Annotated[
        str | None,
        Field(description="Direct biller ID lookup"),
    ] = None,
) -> dict[str, Any]:
    """Look up BBPS (Bharat Bill Payment System) biller details.

    Use when setting up bill payments for electricity, gas, DTH, water,
    broadband, FASTag, insurance, or mobile recharges.

    Args:
            category: Category of biller to filter by.
            state: State to filter by (or 'all' for pan-India).
            biller_id: Direct biller ID for specific lookup.

    Returns:
            Standard envelope with matching billers and parameter schemas.

    Notes:
            Data is bundled offline. For real-time directory, check NPCI BBPS.
    """
    try:
        result = core_lookup_bbps_biller(
            category=category,
            state=state,
            biller_id=biller_id,
        )
        return build_response(
            success=result.get("found", False),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="bundled_dataset",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"BBPS lookup failed: {exc}"],
            source="bundled_dataset",
        )


def main() -> None:
    """Run MCP server with configurable transport."""
    parser = argparse.ArgumentParser(description="mcp-india-stack MCP server")
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help="Refresh all cached datasets from CDN and exit without starting the server.",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport: 'stdio' (local) or 'sse' (HTTP). Default: stdio",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to for SSE transport (default: from $PORT or 8000)",
    )
    args = parser.parse_args()

    if args.refresh_all:
        from mcp_india_stack.utils.updater import force_refresh_all

        print("Refreshing all datasets from CDN...")
        results = force_refresh_all()
        for name, ok in results.items():
            status = "✓ updated" if ok else "✗ failed (using existing data)"
            print(f"  {name}: {status}")
        sys.exit(0)

    if args.transport == "sse":
        from typing import cast

        import uvicorn
        from starlette.middleware.cors import CORSMiddleware

        port = args.port
        if port is None:
            port = int(os.environ.get("PORT", "8000"))

        from mcp.server.fastmcp import FastMCP

        sse_app_instance = cast(FastMCP[Any], mcp).sse_app()

        sse_app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        for route in sse_app_instance.router.routes:
            if hasattr(route, "path") and route.path in ("/sse", ""):
                route.methods = {"GET", "POST"}  # type: ignore[attr-defined]
            if hasattr(route, "path") and route.path in ("/messages", "/messages/"):
                route.methods = {"GET", "POST"}  # type: ignore[attr-defined]

        uvicorn.run(sse_app_instance, host=args.host, port=port)
    else:
        mcp.run(transport="stdio")


@mcp.resource("india://schema/lookup_ifsc")
def schema_lookup_ifsc() -> dict[str, Any]:
    """JSON schema for lookup_ifsc output."""
    return {
        "type": "object",
        "properties": {
            "found": {"type": "boolean"},
            "ifsc": {"type": "string"},
            "bank": {"type": "string"},
            "branch": {"type": "string"},
            "address": {"type": "string"},
            "city": {"type": "string"},
            "district": {"type": "string"},
            "state": {"type": "string"},
            "micr": {"type": "string"},
            "upi_enabled": {"type": "boolean"},
            "rtgs_enabled": {"type": "boolean"},
            "neft_enabled": {"type": "boolean"},
            "imps_enabled": {"type": "boolean"},
            "swift": {"type": "string"},
            "source": {"type": "string"},
            "live_verified": {"type": "boolean"},
            "verification_source": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


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


@mcp.resource("india://schema/lookup_pincode")
def schema_lookup_pincode() -> dict[str, Any]:
    """JSON schema for lookup_pincode output."""
    return {
        "type": "object",
        "properties": {
            "found": {"type": "boolean"},
            "pincode": {"type": "string"},
            "district": {"type": "string"},
            "state": {"type": "string"},
            "post_offices": {"type": "array"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/lookup_hsn_code")
def schema_lookup_hsn_code() -> dict[str, Any]:
    """JSON schema for lookup_hsn_code output."""
    return {
        "type": "object",
        "properties": {
            "found": {"type": "boolean"},
            "code": {"type": "string"},
            "description": {"type": "string"},
            "chapter": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/decode_state_code")
def schema_decode_state_code() -> dict[str, Any]:
    """JSON schema for decode_state_code output."""
    return {
        "type": "object",
        "properties": {
            "found": {"type": "boolean"},
            "state_code": {"type": "string"},
            "state_name": {"type": "string"},
            "abbreviation": {"type": "string"},
            "capital": {"type": "string"},
            "zone": {"type": "string"},
            "errors": {"type": "array", "items": {"type": "string"}},
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


@mcp.resource("india://schema/calculate_income_tax")
def schema_calculate_income_tax() -> dict[str, Any]:
    """JSON schema for calculate_income_tax output."""
    return {
        "type": "object",
        "properties": {
            "gross_income": {"type": "number"},
            "regime": {"type": "string"},
            "taxable_income": {"type": "number"},
            "base_tax": {"type": "number"},
            "surcharge": {"type": "number"},
            "cess": {"type": "number"},
            "total_tax": {"type": "number"},
            "effective_rate": {"type": "number"},
            "take_home": {"type": "number"},
            "monthly_take_home": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_tds")
def schema_calculate_tds() -> dict[str, Any]:
    """JSON schema for calculate_tds output."""
    return {
        "type": "object",
        "properties": {
            "section": {"type": "string"},
            "applicability": {"type": "string"},
            "rate": {"type": "number"},
            "tds_amount": {"type": "number"},
            "net_payment": {"type": "number"},
            "threshold_applicable": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_gst")
def schema_calculate_gst() -> dict[str, Any]:
    """JSON schema for calculate_gst output."""
    return {
        "type": "object",
        "properties": {
            "base_amount": {"type": "number"},
            "gst_rate": {"type": "number"},
            "cgst": {"type": "number"},
            "sgst": {"type": "number"},
            "igst": {"type": "number"},
            "cess": {"type": "number"},
            "total_gst": {"type": "number"},
            "total_amount": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_surcharge")
def schema_calculate_surcharge() -> dict[str, Any]:
    """JSON schema for calculate_surcharge output."""
    return {
        "type": "object",
        "properties": {
            "total_income": {"type": "number"},
            "base_tax": {"type": "number"},
            "surcharge_rate": {"type": "number"},
            "surcharge_before_mrc": {"type": "number"},
            "marginal_relief": {"type": "number"},
            "surcharge_after_mrc": {"type": "number"},
            "cess_base": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_hra_exemption")
def schema_calculate_hra_exemption() -> dict[str, Any]:
    """JSON schema for calculate_hra_exemption output."""
    return {
        "type": "object",
        "properties": {
            "exemption": {"type": "number"},
            "taxable_hra": {"type": "number"},
            "annual_basic_salary": {"type": "number"},
            "annual_hra_received": {"type": "number"},
            "annual_rent_paid": {"type": "number"},
            "city_type": {"type": "string"},
            "is_government_employee": {"type": "boolean"},
            "breakdown": {"type": "object"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_capital_gains")
def schema_calculate_capital_gains() -> dict[str, Any]:
    """JSON schema for calculate_capital_gains output."""
    return {
        "type": "object",
        "properties": {
            "short_term_gains": {"type": "number"},
            "long_term_gains": {"type": "number"},
            "total_gains": {"type": "number"},
            "is_long_term": {"type": "boolean"},
            "holding_period_days": {"type": "integer"},
            "tax_liability": {"type": "number"},
            "asset_type": {"type": "string"},
            "stcg_rate": {"type": "number"},
            "ltcg_rate": {"type": "number"},
            "cost_inflation_adjusted": {"type": "number"},
            "exemption_threshold": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_advance_tax")
def schema_calculate_advance_tax() -> dict[str, Any]:
    """JSON schema for calculate_advance_tax output."""
    return {
        "type": "object",
        "properties": {
            "total_tax_liability": {"type": "number"},
            "existing_tds": {"type": "number"},
            "net_tax_liability": {"type": "number"},
            "advance_tax_due": {"type": "number"},
            "regime": {"type": "string"},
            "taxpayer_type": {"type": "string"},
            "is_advance_tax_required": {"type": "boolean"},
            "installments": {"type": "array"},
            "interest_rules": {"type": "object"},
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


@mcp.prompt()
def vendor_kyc() -> str:
    """Vendor KYC workflow: GSTIN → PAN → IFSC verification.

    Use this workflow to perform comprehensive vendor verification
    by checking GSTIN validity, PAN match, and bank account verification.
    """
    return """You are performing vendor KYC verification for India.

Complete the following verification steps in order:

1. **GSTIN Validation**: Use `validate_gstin` with the vendor's GSTIN.
   - Check if valid and checksum passes
   - Extract embedded PAN from GSTIN

2. **PAN Verification**: Use `validate_pan` with the extracted/complete PAN.
   - Verify PAN format and entity type
   - Ensure PAN matches the GSTIN-embedded PAN

3. **Bank IFSC Verification**: Use `lookup_ifsc` with the vendor's IFSC code.
   - Verify bank branch exists
   - Check RTGS/NEFT/IMPS/UPI enabled status

Provide a consolidated report with:
- GSTIN validity status
- PAN validity and entity type
- Bank verification result
- Overall vendor KYC status: PASS / FAIL / REVIEW_NEEDED
- Any warnings or issues requiring attention

If any step fails, identify the specific issue and recommend next steps."""


@mcp.prompt()
def salary_planner() -> str:
    """Salary planning workflow: income → HRA → tax → take-home.

    Use this workflow to calculate take-home salary with tax optimization.
    """
    return """You are calculating take-home salary for an Indian employee.

Complete the following calculation steps:

1. **Income Input**: Gather user's annual gross income.

2. **HRA Exemption Calculation**: Use HRA exemption calculator with:
   - Actual HRA received
   - Rent paid
   - City type (metro vs non-metro)
   - Apply 40%/50% of salary rule

3. **Tax Computation**: Use `calculate_income_tax` with:
   - Gross income
   - Regime: compare 'both' new vs old
   - Include HRA exemption (if self-owned, use 24b instead)
   - Deductions: 80C, 80D, NPS, etc.

4. **Take-Home Calculation**:
   - Gross - Total Tax = Net taxable income
   - Divide by 12 for monthly take-home

Provide a consolidated report with:
- Gross annual income
- HRA exemption amount
- Taxable income after deductions
- Tax liability under both regimes
- Recommended regime (new vs old)
- Monthly take-home for recommended regime
- Annual CTC breakdown
- Tax optimization suggestions"""


@mcp.prompt()
def invoice_audit() -> str:
    """Invoice audit workflow: GSTIN → HSN → GST rate validation.

    Use this workflow to validate invoice tax compliance.
    """
    return """You are performing invoice tax compliance audit for India.

Complete the following validation steps:

1. **GSTIN Format Check**: Use `validate_gstin` with supplier's GSTIN.
   - Verify format and checksum
   - Extract state code and entity type

2. **HSN Code Lookup**: Use `lookup_hsn_code` with:
   - Product/service HSN code (4, 6, or 8 digit)
   - Or search by keyword

3. **GST Rate Validation**:
   - Map HSN to applicable GST rate (0%, 5%, 12%, 18%, 28%)
   - Verify against invoice GST rate
   - Check for cess applicability on 28% items

4. **Invoice Summary**:
   - Validate GSTIN format
   - Verify HSN code exists and maps to rate
   - Confirm GST rate matches HSN classification
   - Identify any discrepancies

Provide a consolidated report with:
- Supplier GSTIN validity
- HSN code and description
- Applicable GST rate
- Invoice GST rate match: YES / NO
- Compliance status: COMPLIANT / NON_COMPLIANT / REVIEW_NEEDED
- List of issues requiring correction"""


# ========== Server Status and Resources ==========

import os as _os

_DRY_RUN = _os.environ.get("MCP_INDIA_STACK_DRY_RUN") == "1"
_LIVE_LOOKUP_ENABLED = _os.environ.get("MCP_INDIA_STACK_LIVE_LOOKUP") == "1"
_DB_URL_SET = _os.environ.get("MCP_INDIA_STACK_DB_URL") is not None

from mcp_india_stack import __version__
from mcp_india_stack.database import is_db_connected


@mcp.resource("india://status")
def server_status() -> dict[str, Any]:
    """Server status and configuration."""
    return {
        "version": __version__,
        "db_connected": is_db_connected(),
        "live_lookup_enabled": _LIVE_LOOKUP_ENABLED,
        "dry_run_mode": _DRY_RUN,
        "db_url_configured": _DB_URL_SET,
        "tool_count": 30,
        "data_version": "2025.04",
    }


@mcp.resource("india://changelog")
def changelog() -> dict[str, Any]:
    """Structured changelog as JSON."""
    return {
        "current_version": "0.3.0",
        "entries": [
            {
                "version": "0.3.0",
                "date": "2026-04-28",
                "changes": [
                    "Added ToolAnnotations to all tools",
                    "Added PermissionTier enum",
                    "Added opt-in live GSTN/IFSC lookup",
                    "Added bulk_validate_gstin",
                    "Added HRA, Capital Gains, Advance Tax calculators",
                    "Added BBPS biller directory",
                    "Added structured telemetry",
                    "Added input normalization layer",
                    "Added confidence scoring",
                    "Added server status resource",
                ],
            },
            {
                "version": "0.2.0",
                "date": "2024-12",
                "changes": [
                    "Initial release with 17 tools",
                ],
            },
        ],
    }


# ========== New Tools ==========


def _validate_single_pan(pan: str) -> dict[str, Any]:
    """Validate a single PAN with error isolation."""
    from mcp_india_stack.tools import validate_pan as _validate_pan

    try:
        return _validate_pan(pan)
    except Exception as exc:
        return {"valid": False, "pan": pan, "errors": [f"Validation error: {exc}"], "warnings": []}


def _validate_single_ifsc(ifsc: str) -> dict[str, Any]:
    """Validate a single IFSC with error isolation."""
    from mcp_india_stack.tools import lookup_ifsc as _lookup_ifsc

    try:
        return _lookup_ifsc(ifsc)
    except Exception as exc:
        return {"found": False, "ifsc": ifsc, "errors": [f"Lookup error: {exc}"], "warnings": []}


_BULK_WORKERS = int(_os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10"))


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def bulk_validate_pan(
    pans: Annotated[list[str], Field(description="List of PANs to validate (max 500)")],
) -> dict[str, Any]:
    """Validate multiple PANs in parallel. # PermissionTier: READ_ONLY"""
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


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def bulk_validate_ifsc(
    ifscs: Annotated[list[str], Field(description="List of IFSC codes to validate (max 500)")],
) -> dict[str, Any]:
    """Validate multiple IFSC codes in parallel. # PermissionTier: READ_ONLY"""
    if not ifscs:
        return build_response(success=False, data=None, errors=["Empty IFSC list"])
    if len(ifscs) > 500:
        return build_response(success=False, data=None, errors=["Maximum 500 IFSCs per call"])

    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []
    found_count = 0

    with ThreadPoolExecutor(max_workers=_BULK_WORKERS) as executor:
        futures = {
            executor.submit(_validate_single_ifsc, ifsc): idx for idx, ifsc in enumerate(ifscs)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append((futures[future], result))
            if result.get("found"):
                found_count += 1

    results.sort(key=lambda x: x[0])
    ordered_results = [r for _, r in results]

    return build_response(
        success=True,
        data={"results": ordered_results, "total": len(ifscs), "found_count": found_count},
        source="offline_algorithm",
    )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def decode_pan_type(
    pan: Annotated[str, Field(description="10-character PAN")],
) -> dict[str, Any]:
    """Decode PAN entity type from 4th character. # PermissionTier: READ_ONLY"""
    from mcp_india_stack.tools.pan import validate_pan

    result = validate_pan(pan)

    if result.get("valid"):
        entity_code = result.get("entity_code", "")
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
        success=False,
        data=result,
        errors=result.get("errors", []),
        source="offline_algorithm",
    )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def lookup_bank(
    name_or_code: Annotated[str, Field(description="Bank name or IFSC code prefix")],
) -> dict[str, Any]:
    """Look up bank details from RBI master list. # PermissionTier: READ_ONLY"""
    # Bundled bank master data (sample)
    banks: list[dict[str, Any]] = [
        {
            "name": "State Bank of India",
            "code": "SBIN",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "HDFC Bank Limited",
            "code": "HDFC",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "ICICI Bank Limited",
            "code": "ICICI",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "Punjab National Bank",
            "code": "PNB",
            "type": "commercial",
            "hq": "New Delhi",
            "rbi_licensed": True,
        },
        {
            "name": "Bank of Baroda",
            "code": "BARODA",
            "type": "commercial",
            "hq": "Vadodara",
            "rbi_licensed": True,
        },
        {
            "name": "Canara Bank",
            "code": "CANARA",
            "type": "commercial",
            "hq": "Bengaluru",
            "rbi_licensed": True,
        },
        {
            "name": "Axis Bank Limited",
            "code": "AXIS",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "Kotak Mahindra Bank",
            "code": "KOTAK",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "Yes Bank Limited",
            "code": "YES",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
        {
            "name": "IDBI Bank Limited",
            "code": "IDBI",
            "type": "commercial",
            "hq": "Mumbai",
            "rbi_licensed": True,
        },
    ]

    search = name_or_code.upper().strip()
    matches = [b for b in banks if search in b["name"].upper() or search in b["code"]]

    return build_response(
        success=len(matches) > 0,
        data={"banks": matches, "count": len(matches)},
        source="bundled_dataset",
    )


# ========== EPF/ESIC Validators ==========

import re as _re

EPF_RE = _re.compile(r"^\d{2}/\d{5,6}/\d{5,6}/\d{3}$")
ESIC_RE = _re.compile(r"^[\d]{2}-[\d]+-[\d]+$")


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_epf_code(
    code: Annotated[str, Field(description="EPF establishment code (XX/XXXXX/XXXXXX/XXX)")],
) -> dict[str, Any]:
    """Validate EPF establishment code. # PermissionTier: READ_ONLY"""
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


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_esic_code(
    code: Annotated[str, Field(description="ESIC employer code (XX-XXXXX-XXXXX)")],
) -> dict[str, Any]:
    """Validate ESIC employer code. # PermissionTier: READ_ONLY"""
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


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def decode_digilocker_uri(
    uri: Annotated[str, Field(description="DigiLocker document URI")],
) -> dict[str, Any]:
    """Decode DigiLocker document URI and map to validator. # PermissionTier: READ_ONLY"""
    errors = []
    warnings = []

    if not uri.startswith("dlg://"):
        errors.append("Invalid DigiLocker URI format. Must start with 'dlg://'")
        return build_response(success=False, data=None, errors=errors, source="offline_algorithm")

    # Parse URI
    path = uri.replace("dlg://", "")
    parts = path.split("/")

    if len(parts) < 2:
        errors.append("Invalid DigiLocker URI format")
        return build_response(success=False, data=None, errors=errors, source="offline_algorithm")

    issuer = parts[0].lower()
    doc_type = parts[1].lower() if len(parts) > 1 else ""

    # Map to validators
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


# ========== Dry-Run Mode Handler ==========

if _DRY_RUN:
    print("[DRY RUN MODE] All tool responses will be synthetic")
