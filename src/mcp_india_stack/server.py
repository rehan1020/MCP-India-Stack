"""FastMCP server for mcp-india-stack."""

from __future__ import annotations

import argparse
import sys
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from mcp_india_stack.tools import (
    calculate_gst as core_calculate_gst,
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
    validate_din as core_validate_din,
)
from mcp_india_stack.tools import (
    validate_driving_license as core_validate_driving_license,
)
from mcp_india_stack.tools import (
    validate_gstin as core_validate_gstin,
)
from mcp_india_stack.tools import (
    validate_pan as core_validate_pan,
)
from mcp_india_stack.tools import (
    validate_passport as core_validate_passport,
)
from mcp_india_stack.tools import (
    validate_upi_vpa as core_validate_upi_vpa,
)
from mcp_india_stack.tools import (
    validate_voter_id as core_validate_voter_id,
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


@mcp.tool()
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


@mcp.tool()
def validate_gstin(
    gstin: Annotated[
        str,
        Field(min_length=15, max_length=15, description="15-character GSTIN"),
    ],
) -> dict[str, Any]:
    """Validate and decode an Indian GSTIN with checksum verification.

    Use when checking supplier/customer GSTINs before invoicing, reconciliation,
    or compliance workflows.

    Args:
            gstin: 15-character GSTIN, example: 27AAPFU0939F1ZV.

    Returns:
            Standard envelope containing validity, state decode, embedded PAN,
            entity number, category, and checksum information.

    Notes:
            Validates structure and checksum only; does not verify active GSTN registration status.
    """
    try:
        result = core_validate_gstin(gstin)
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
            errors=[f"GSTIN validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_pan(
    pan: Annotated[str, Field(min_length=10, max_length=10, description="10-char PAN")],
) -> dict[str, Any]:
    """Validate Indian PAN format and decode entity type from the 4th character.

    Use when normalizing tax identity records in KYC, invoicing, or vendor onboarding.

    Args:
            pan: PAN string, example: AAAPL1234C.

    Returns:
            Standard envelope containing format validity, entity type, and decoded segments.

    Notes:
            PAN check character is not publicly verifiable algorithmically.
    """
    try:
        result = core_validate_pan(pan)
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
def validate_aadhaar(
    aadhaar: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description=(
                "12-digit Aadhaar number. Spaces and hyphens accepted. "
                "Example: 2959 4583 7261"
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
    try:
        result = core_validate_aadhaar(aadhaar)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Aadhaar validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_voter_id(
    voter_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="10-character EPIC number. Example: ABC1234567",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian Voter ID (EPIC) number format.

    Use when verifying voter ID format in KYC, identity, or electoral workflows.

    Args:
            voter_id: EPIC number, 3 uppercase letters + 7 digits.

    Returns:
            Standard envelope containing validity, prefix, serial, and format type.

    Notes:
            Format validation only. Detects possible legacy EPIC formats.
    """
    try:
        result = core_validate_voter_id(voter_id)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Voter ID validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_driving_license(
    dl_number: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="Indian DL number, 15 chars standard. Example: MH0220191234567",
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
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"DL validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_passport(
    passport_number: Annotated[
        str,
        Field(
            min_length=1,
            max_length=12,
            description="8-character Indian passport number. Example: A1234567",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian passport number format.

    Use when verifying passport format in KYC, travel, or identity workflows.

    Args:
            passport_number: 1 letter + 7 digits.

    Returns:
            Standard envelope containing validity, series letter, and serial number.

    Notes:
            Format validation only. No public checksum algorithm exists.
    """
    try:
        result = core_validate_passport(passport_number)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Passport validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_cin(
    cin: Annotated[
        str,
        Field(
            min_length=1,
            max_length=25,
            description="21-character CIN. Example: L17110MH1973PLC019786",
        ),
    ],
) -> dict[str, Any]:
    """Validate and decode an Indian CIN (Company Identification Number).

    Use when verifying company registration data, extracting listing status,
    NIC code, state, year, and company type from a CIN.

    Args:
            cin: 21-character CIN string.

    Returns:
            Standard envelope containing decoded fields: listing status, NIC code,
            state, year of incorporation, company type, and serial number.

    Notes:
            Format validation with field decoding. No public checksum.
    """
    try:
        result = core_validate_cin(cin)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"CIN validation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool()
def validate_din(
    din: Annotated[
        str,
        Field(
            min_length=1,
            max_length=12,
            description="8-digit DIN. Example: 00012345",
        ),
    ],
) -> dict[str, Any]:
    """Validate an Indian DIN (Director Identification Number) format.

    Use when verifying director identity numbers in MCA compliance workflows.

    Args:
            din: 8-digit numeric DIN string. Shorter inputs are zero-padded.

    Returns:
            Standard envelope containing validity and normalized DIN.

    Notes:
            Format validation only. Cannot verify director status with MCA.
    """
    try:
        result = core_validate_din(din)
        return build_response(
            success=bool(result.get("valid")),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"DIN validation failed: {exc}"],
            source="offline_algorithm",
        )


# ---------------------------------------------------------------------------
# v0.2.0 — Tax calculation tools
# ---------------------------------------------------------------------------


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


def main() -> None:
    """Run MCP server on stdio transport."""
    parser = argparse.ArgumentParser(description="mcp-india-stack MCP server")
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help="Refresh all cached datasets from CDN and exit without starting the server.",
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

    mcp.run(transport="stdio")
