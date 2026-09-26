from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.hsn import lookup_hsn_code as core_lookup_hsn_code
from mcp_india_stack.tools.isin import decode_isin as core_decode_isin
from mcp_india_stack.tools.pincode import lookup_pincode as core_lookup_pincode
from mcp_india_stack.tools.state_code import decode_state_code as core_decode_state_code
from mcp_india_stack.utils.responses import build_response


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
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
            success=False, errors=[f"Pincode lookup failed: {exc}"], source="bundled_dataset"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_hsn_code(
    code: Annotated[
        str | None, Field(default=None, description="HSN/SAC code (2-8 digits) for exact lookup")
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
            success=False, errors=[f"HSN lookup failed: {exc}"], source="bundled_dataset"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_state_code(
    value: Annotated[
        str, Field(min_length=2, max_length=15, description="2-digit state code or GSTIN")
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
            success=False, errors=[f"State code decode failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_isin(
    isin: Annotated[str, Field(description="12-character ISIN (e.g., INE1234567890)")],
) -> dict[str, Any]:
    """Decode ISIN (International Securities Identification Number) with Luhn check.

    Use when validating ISIN for Indian securities.

    Args:
        isin: 12-character ISIN

    Returns:
        Decoded fields with country, NSIN, security type, and Luhn validation.
    """
    try:
        result = core_decode_isin(isin)
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"ISIN decode failed: {exc}"], source="offline_algorithm"
        )


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
