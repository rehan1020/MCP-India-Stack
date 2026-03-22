"""FastMCP server for mcp-india-stack."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

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
        "validation and lookup for GSTIN, IFSC, PAN, UPI VPA, India pincodes, "
        "HSN/SAC codes, and state codes. Zero authentication required."
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


def main() -> None:
    """Run MCP server on stdio transport."""
    mcp.run(transport="stdio")
