"""FastMCP application instance for mcp-india-stack.

This module creates and configures the shared FastMCP instance used by all
registration modules. It also defines the TOOL_TIERS permission map and the
cross-cutting _wrapped_mcp_tool decorator that enforces tier-based gating,
telemetry logging, and latency profiling.
"""

from __future__ import annotations

import functools
import os
import time
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations  # noqa: F401 — re-exported for registrations

from mcp_india_stack.permission_tiers import PermissionTier
from mcp_india_stack.telemetry import log_tool_usage

mcp = FastMCP(
    name="mcp-india-stack",
    instructions=(
        "Indian financial and government data tools for AI agents. Provides offline "
        "validation for GSTIN, IFSC, PAN, UPI VPA, Aadhaar, Voter ID, DL, Passport, "
        "CIN, DIN; tax calculators for income tax, TDS, GST, surcharge; and lookups "
        "for pincodes, HSN/SAC codes, and state codes. Zero authentication required."
    ),
)

_ELEVATED_ENABLED = os.environ.get("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", "0").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

TOOL_TIERS: dict[str, PermissionTier] = {
    "lookup_ifsc": PermissionTier.LOOKUP_LIVE,
    "validate_gstin": PermissionTier.READ_ONLY,
    "bulk_validate_gstin": PermissionTier.READ_ONLY,
    "validate_pan": PermissionTier.READ_ONLY,
    "validate_upi_vpa": PermissionTier.READ_ONLY,
    "lookup_pincode": PermissionTier.READ_ONLY,
    "lookup_hsn_code": PermissionTier.READ_ONLY,
    "decode_state_code": PermissionTier.READ_ONLY,
    "validate_aadhaar": PermissionTier.READ_ONLY,
    "validate_voter_id": PermissionTier.READ_ONLY,
    "validate_driving_license": PermissionTier.READ_ONLY,
    "validate_passport": PermissionTier.READ_ONLY,
    "validate_cin": PermissionTier.READ_ONLY,
    "validate_din": PermissionTier.READ_ONLY,
    "validate_fssai": PermissionTier.READ_ONLY,
    "calculate_income_tax": PermissionTier.READ_ONLY,
    "calculate_tds": PermissionTier.READ_ONLY,
    "calculate_gst": PermissionTier.READ_ONLY,
    "calculate_surcharge": PermissionTier.READ_ONLY,
    "calculate_hra_exemption": PermissionTier.READ_ONLY,
    "calculate_capital_gains": PermissionTier.READ_ONLY,
    "calculate_advance_tax": PermissionTier.READ_ONLY,
    "lookup_bbps_biller": PermissionTier.READ_ONLY,
    "calculate_epf_esic": PermissionTier.READ_ONLY,
    "calculate_emi": PermissionTier.READ_ONLY,
    "calculate_gratuity": PermissionTier.READ_ONLY,
    "calculate_ppf_maturity": PermissionTier.READ_ONLY,
    "bulk_validate_aadhaar": PermissionTier.READ_ONLY,
    "get_regulatory_deadlines": PermissionTier.READ_ONLY,
    "calculate_salary_restructuring": PermissionTier.READ_ONLY,
    "bulk_validate_pan": PermissionTier.READ_ONLY,
    "bulk_validate_ifsc": PermissionTier.LOOKUP_LIVE,
    "decode_pan_type": PermissionTier.READ_ONLY,
    "lookup_bank": PermissionTier.READ_ONLY,
    "validate_epf_code": PermissionTier.READ_ONLY,
    "validate_esic_code": PermissionTier.READ_ONLY,
    "decode_digilocker_uri": PermissionTier.READ_ONLY,
    "build_aa_consent_request": PermissionTier.INITIATE,
    "validate_aa_consent_artifact": PermissionTier.READ_ONLY,
    "decode_aa_fi_type": PermissionTier.READ_ONLY,
    "calculate_fd_maturity": PermissionTier.READ_ONLY,
    "calculate_rd_maturity": PermissionTier.READ_ONLY,
    "calculate_sip_returns": PermissionTier.READ_ONLY,
    "calculate_step_up_sip": PermissionTier.READ_ONLY,
    "calculate_nps_projection": PermissionTier.READ_ONLY,
    "calculate_sukanya_samriddhi": PermissionTier.READ_ONLY,
    "calculate_home_vs_rent": PermissionTier.READ_ONLY,
    "calculate_gst_late_fee": PermissionTier.READ_ONLY,
    "calculate_income_tax_interest": PermissionTier.READ_ONLY,
    "calculate_presumptive_tax": PermissionTier.READ_ONLY,
    "calculate_professional_tax": PermissionTier.READ_ONLY,
    "calculate_leave_encashment_tax": PermissionTier.READ_ONLY,
    "validate_tan": PermissionTier.READ_ONLY,
    "validate_mobile_number": PermissionTier.READ_ONLY,
    "validate_pran": PermissionTier.READ_ONLY,
    "validate_llpin": PermissionTier.READ_ONLY,
    "decode_isin": PermissionTier.READ_ONLY,
    "calculate_neft_rtgs_imps_charges": PermissionTier.READ_ONLY,
    "get_stock_quote": PermissionTier.LOOKUP_LIVE,
    "get_stock_history": PermissionTier.LOOKUP_LIVE,
    "decode_cnr_number": PermissionTier.READ_ONLY,
    "lookup_court_establishment_code": PermissionTier.READ_ONLY,
    "lookup_ipc_section": PermissionTier.READ_ONLY,
    "lookup_bns_section": PermissionTier.READ_ONLY,
    "lookup_crpc_section": PermissionTier.READ_ONLY,
    "lookup_bnss_section": PermissionTier.READ_ONLY,
    "lookup_evidence_act_section": PermissionTier.READ_ONLY,
    "lookup_bsa_section": PermissionTier.READ_ONLY,
    "decode_ipc_bns_crosswalk": PermissionTier.READ_ONLY,
    "calculate_limitation_deadline": PermissionTier.READ_ONLY,
    "calculate_court_fee": PermissionTier.READ_ONLY,
    "calculate_stamp_duty": PermissionTier.READ_ONLY,
    "calculate_rti_fee": PermissionTier.READ_ONLY,
    "calculate_rti_deadline": PermissionTier.READ_ONLY,
    "calculate_rti_penalty_estimate": PermissionTier.READ_ONLY,
    "draft_rti_application": PermissionTier.INITIATE,
    "draft_first_appeal": PermissionTier.INITIATE,
    "draft_second_appeal": PermissionTier.INITIATE,
}

_original_mcp_tool = mcp.tool


def _wrapped_mcp_tool(
    name: str | None = None,
    description: str | None = None,
    annotations: Any = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or func.__name__
        tier = TOOL_TIERS.get(tool_name)

        if tier is None:
            msg = (
                f"Server refused to start: Tool '{tool_name}' "
                "lacks a PermissionTier classification."
            )
            raise RuntimeError(msg)

        if not _ELEVATED_ENABLED and tier in (PermissionTier.INITIATE, PermissionTier.SUBMIT):
            return func  # Skip registering this tool with MCP

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            success = False
            result_type = "error"
            input_value = None

            # Simple heuristic for identifier: first positional string arg, or first kwarg string
            if args and isinstance(args[0], str):
                input_value = args[0]
            elif kwargs:
                for v in kwargs.values():
                    if isinstance(v, str):
                        input_value = v
                        break

            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict):
                    success = result.get("success", False)
                    if (
                        "data" in result
                        and isinstance(result["data"], dict)
                        and "found" in result["data"]
                    ):
                        result_type = "found" if result["data"]["found"] else "not_found"
                    else:
                        result_type = "success" if success else "invalid"
                else:
                    success = True
                    result_type = "success"
                return result
            except Exception:
                success = False
                result_type = "error"
                raise
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                log_tool_usage(tool_name, input_value, latency_ms, result_type)

        return _original_mcp_tool(name=tool_name, description=description, annotations=annotations)(
            wrapper
        )

    return decorator


mcp.tool = _wrapped_mcp_tool  # type: ignore[method-assign, assignment]
