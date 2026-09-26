import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.aa_consent import (
    build_aa_consent_request as core_build_aa_consent_request,
)
from mcp_india_stack.tools.aa_fi_type import decode_aa_fi_type as core_decode_aa_fi_type
from mcp_india_stack.tools.bank_charges import (
    calculate_neft_rtgs_imps_charges as core_calculate_neft_rtgs_imps_charges,
)
from mcp_india_stack.tools.bbps import lookup_bbps_biller as core_lookup_bbps_biller
from mcp_india_stack.tools.epf_esic import calculate_epf_esic as core_calculate_epf_esic
from mcp_india_stack.tools.ifsc import lookup_ifsc as core_lookup_ifsc
from mcp_india_stack.utils.responses import build_response


def _validate_single_ifsc(ifsc: str) -> dict[str, Any]:
    """Validate a single IFSC with error isolation."""
    from mcp_india_stack.tools import lookup_ifsc as _lookup_ifsc

    try:
        return _lookup_ifsc(ifsc)
    except Exception as exc:
        return {"found": False, "ifsc": ifsc, "errors": [f"Lookup error: {exc}"], "warnings": []}


def _clamp_bulk_workers() -> int:
    """Parse MCP_INDIA_STACK_BULK_WORKERS with hard [1, 20] clamp."""
    raw = os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 10
    return max(1, min(20, val))


_BULK_WORKERS = _clamp_bulk_workers()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
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


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def bulk_validate_ifsc(
    ifscs: Annotated[list[str], Field(description="List of IFSC codes to validate (max 500)")],
) -> dict[str, Any]:
    """Validate multiple IFSC codes in parallel."""
    if not ifscs:
        return build_response(success=False, data=None, errors=["Empty IFSC list"])
    if len(ifscs) > 500:
        return build_response(success=False, data=None, errors=["Maximum 500 IFSCs per call"])
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


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_bbps_biller(
    category: Annotated[
        str | None,
        Field(description="electricity, gas, dth, water, broadband, fastag, insurance, mobile"),
    ] = None,
    state: Annotated[
        str | None, Field(description="State name (e.g., 'Maharashtra', 'Delhi') or 'all'")
    ] = None,
    biller_id: Annotated[str | None, Field(description="Direct biller ID lookup")] = None,
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
        result = core_lookup_bbps_biller(category=category, state=state, biller_id=biller_id)
        return build_response(
            success=result.get("found", False),
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="bundled_dataset",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"BBPS lookup failed: {exc}"], source="bundled_dataset"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_epf_esic(
    basic_wages: Annotated[float, Field(description="Basic salary + DA per month in INR")],
    gross_wages: Annotated[float, Field(description="Total gross monthly salary in INR")],
    include_employer_share: Annotated[
        bool, Field(description="If True, return employer costs")
    ] = True,
) -> dict[str, Any]:
    """Calculate EPF and ESIC contributions for employer and employee.

    Use when computing payroll costs, employee deductions, or comparing
    CTC structures across different salary levels.

    Args:
        basic_wages: Basic salary + DA per month in INR.
        gross_wages: Total gross monthly salary in INR.
        include_employer_share: If True, return employer costs.

    Returns:
        Standard envelope with EPF breakdown, ESIC applicability, and totals.

    Notes:
        EPF ceiling is ₹15,000/month for statutory computation.
        ESIC applicable when gross wages ≤ ₹21,000/month.
    """
    try:
        result = core_calculate_epf_esic(
            basic_wages=basic_wages,
            gross_wages=gross_wages,
            include_employer_share=include_employer_share,
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
            errors=[f"EPF/ESIC calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_neft_rtgs_imps_charges(
    transfer_mode: Annotated[str, Field(description="NEFT, RTGS, IMPS, or UPI")],
    amount: Annotated[float, Field(description="Transfer amount in INR")],
    account_type: Annotated[str, Field(description="'savings' or 'current'")] = "savings",
    is_online: Annotated[bool, Field(description="True if done via online banking")] = True,
) -> dict[str, Any]:
    """Calculate NEFT/RTGS/IMPS/UPI transaction charges.

    Use when estimating bank transfer costs or comparing payment modes.

    Args:
        transfer_mode: "NEFT", "RTGS", "IMPS", or "UPI"
        amount: Transfer amount in INR
        account_type: "savings" or "current"
        is_online: True if done via online banking

    Returns:
        Charge breakdown with base charge, GST, and total.
    """
    try:
        result = core_calculate_neft_rtgs_imps_charges(
            transfer_mode=transfer_mode,
            amount=amount,
            account_type=account_type,
            is_online=is_online,
        )
        return build_response(
            success="errors" not in result,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Bank charges calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_bank(
    name_or_code: Annotated[str, Field(description="Bank name or IFSC code prefix")],
) -> dict[str, Any]:
    """Look up bank details from RBI master list."""
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


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def build_aa_consent_request(
    customer_id: Annotated[str, Field(description="AA customer address (e.g., user@onemoney)")],
    fi_types: Annotated[
        list[str],
        Field(
            description="FI types: DEPOSIT, MUTUAL_FUNDS, INSURANCE, NPS, EQUITIES, GSTIN_DATA, CREDIT_CARD, RECURRING_DEPOSIT"  # noqa: E501
        ),
    ],
    date_range_from: Annotated[str, Field(description="Start date YYYY-MM-DD")],
    date_range_to: Annotated[str, Field(description="End date YYYY-MM-DD")],
    consent_expiry_days: Annotated[int, Field(description="Days until consent expires")] = 30,
    purpose_code: Annotated[str, Field(description="ReBIT purpose code (101-106)")] = "101",
    fetch_type: Annotated[str, Field(description="ONETIME or PERIODIC")] = "ONETIME",
    frequency_unit: Annotated[
        str | None, Field(description="HOUR, DAY, MONTH, YEAR for PERIODIC")
    ] = None,
    frequency_value: Annotated[
        int | None, Field(description="Frequency value for PERIODIC")
    ] = None,
) -> dict[str, Any]:
    """Build AA (Account Aggregator) consent request JSON per ReBIT spec.

    Use when setting up data sharing consent for open banking workflows.

    Args:
        customer_id: AA customer address (user@provider)
        fi_types: Financial information types to request
        date_range_from: Data fetch range start
        date_range_to: Data fetch range end
        consent_expiry_days: How many days consent remains valid
        purpose_code: ReBIT purpose code (default "101")
        fetch_type: "ONETIME" or "PERIODIC"
        frequency_unit: "HOUR", "DAY", "MONTH", "YEAR" - for PERIODIC
        frequency_value: Numeric frequency - for PERIODIC

    Returns:
        Consent request payload and validation notes.
    """
    try:
        result = core_build_aa_consent_request(
            customer_id=customer_id,
            fi_types=fi_types,
            date_range_from=date_range_from,
            date_range_to=date_range_to,
            consent_expiry_days=consent_expiry_days,
            purpose_code=purpose_code,
            fetch_type=fetch_type,
            frequency_unit=frequency_unit,
            frequency_value=frequency_value,
        )
        return build_response(
            success=result.get("valid", False),
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"AA consent request failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def validate_aa_consent_artifact(
    artifact: Annotated[dict[str, Any], Field(description="AA consent artifact JSON")],
) -> dict[str, Any]:
    """Validate AA consent artifact structure and flags.

    Use when verifying consent artifacts received from AA before processing.

    Args:
        artifact: Consent artifact JSON from AA response

    Returns:
        Validation result with consent details.
    """
    from mcp_india_stack.tools.aa_consent import FI_TYPE_VALID, PURPOSE_CODE_MAP

    errors = []
    warnings = []
    if "consentStart" not in artifact:
        errors.append("Missing consentStart")
    if "consentExpiry" not in artifact:
        errors.append("Missing consentExpiry")
    if "fiTypes" not in artifact:
        errors.append("Missing fiTypes")
    elif not isinstance(artifact.get("fiTypes"), list):
        errors.append("fiTypes must be a list")
    else:
        for ft in artifact.get("fiTypes", []):
            if ft not in FI_TYPE_VALID:
                warnings.append(f"Unknown fi_type: {ft}")
    if "Purpose" in artifact and artifact["Purpose"].get("code") not in PURPOSE_CODE_MAP:
        warnings.append(f"Unknown purpose code: {artifact['Purpose'].get('code')}")
    return build_response(
        success=len(errors) == 0,
        data={
            "artifact": artifact,
            "errors": errors,
            "warnings": warnings,
            "validated": len(errors) == 0,
        },
        source="offline_algorithm",
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_aa_fi_type(
    fi_type: Annotated[str, Field(description="FI type code (e.g., DEPOSIT, MUTUAL_FUNDS)")],
) -> dict[str, Any]:
    """Decode AA Financial Information type and get MCP tool pairings.

    Use when mapping FI types to validation/calculation tools.

    Args:
        fi_type: FI type code (e.g., "DEPOSIT", "MUTUAL_FUNDS")

    Returns:
        FI type description, typical fields, and MCP tool pairings.
    """
    try:
        result = core_decode_aa_fi_type(fi_type)
        return build_response(
            success=result.get("description") is not None,
            data=result,
            errors=[str(result.get("error"))] if result.get("error") else [],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"FI type decode failed: {exc}"], source="offline_algorithm"
        )


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
