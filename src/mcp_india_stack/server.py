"""FastMCP server entry point for mcp-india-stack.

This is a thin entry point that:
- Imports the shared FastMCP instance from app.py
- Triggers tool registration via the registrations/ package
- Defines server-level resources, prompt templates, and the CLI runner
- Wires CORS, auth, and rate-limit middleware for SSE transport
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from typing import Any

# Trigger side-effect registration of all 78 tools
import mcp_india_stack.registrations  # noqa: F401
from mcp_india_stack import __version__
from mcp_india_stack.app import mcp
from mcp_india_stack.database import is_db_connected

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment flags for server status
# ---------------------------------------------------------------------------
_DRY_RUN = os.environ.get("MCP_INDIA_STACK_DRY_RUN") == "1"
_LIVE_LOOKUP_ENABLED = os.environ.get("MCP_INDIA_STACK_LIVE_LOOKUP") == "1"
_DB_URL_SET = os.environ.get("MCP_INDIA_STACK_DB_URL") is not None


# ---------------------------------------------------------------------------
# Server-level resources
# ---------------------------------------------------------------------------


@mcp.resource("india://status")
def server_status() -> dict[str, Any]:
    """Server status and configuration."""
    return {
        "version": __version__,
        "db_connected": is_db_connected(),
        "live_lookup_enabled": _LIVE_LOOKUP_ENABLED,
        "dry_run_mode": _DRY_RUN,
        "db_url_configured": _DB_URL_SET,
        "tool_count": 78,
        "data_version": "2025.04",
    }


@mcp.resource("india://changelog")
def changelog() -> dict[str, Any]:
    """Structured changelog as JSON."""
    return {
        "current_version": __version__,
                "entries": [
            {
                "version": "0.6.7",
                "date": "2026-10-02",
                "changes": [
                    "Update 5/7: Decomposed server.py by domain",
                    "Extracted 7 registration modules (kyc, tax, banking, finance, etc)",
                    "Extracted inline tools (esic_code, epf_code, digilocker, etc) to tools dir"
                ]
            },
            {
                "version": "0.6.6",
                "date": "2026-10-02",
                "changes": [
                    "Update 4/7: Centralized normalization pipeline",
                    "Routed UPI and pincode through shared normalizer",
                    "Hoisted local normalization imports to module level",
                ],
            },
            {
                "version": "0.6.5",
                "date": "2026-09-21",
                "changes": [
                    "Update 3/7: Resolved dead/unsafe scaffolding",
                    "Removed insecure raw-SQL execution from database.py",
                    "Redesigned telemetry with HMAC-SHA256 pseudonymization",
                    "Implemented Permission Tier classification for all 78 tools",
                ],
            },
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


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# CLI entry point & middleware
# ---------------------------------------------------------------------------


def main() -> None:  # noqa: C901
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
        import uvicorn
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.middleware.cors import CORSMiddleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        sse_logger = logging.getLogger("mcp_india_stack")

        port = args.port
        if port is None:
            port = int(os.environ.get("PORT", "8000"))

        sse_app_instance = mcp.sse_app()

        # --- CORS hardening ---
        _raw_origins = os.environ.get("MCP_INDIA_STACK_ALLOWED_ORIGINS", "").strip()
        _allowed_origins = (
            [o.strip() for o in _raw_origins.split(",") if o.strip()] if _raw_origins else []
        )
        _allow_creds = bool(_allowed_origins)

        if _allow_creds and "*" in _allowed_origins:
            raise RuntimeError(
                "CORS misconfiguration: allow_origins=['*'] with "
                "allow_credentials=True is forbidden. Set explicit "
                "origins in MCP_INDIA_STACK_ALLOWED_ORIGINS."
            )

        sse_app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=_allowed_origins,
            allow_credentials=_allow_creds,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

        # --- Rate limiting middleware ---
        class _RateLimitMiddleware(BaseHTTPMiddleware):
            def __init__(self, app: Any, max_requests: int = 60, window_seconds: int = 60) -> None:
                super().__init__(app)
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self._buckets: dict[str, list[float]] = {}
                self._lock = threading.Lock()

            def _get_key(self, request: Request) -> str:
                auth = request.headers.get("Authorization", "")
                if auth.startswith("Bearer "):
                    return f"key:{auth[7:]}"
                return f"ip:{request.client.host}" if request.client else "ip:unknown"

            async def dispatch(self, request: Request, call_next: Any) -> Any:
                key = self._get_key(request)
                now = time.monotonic()
                with self._lock:
                    timestamps = self._buckets.setdefault(key, [])
                    cutoff = now - self.window_seconds
                    timestamps[:] = [t for t in timestamps if t > cutoff]
                    if len(timestamps) >= self.max_requests:
                        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
                    timestamps.append(now)
                response: Any = await call_next(request)
                return response

        _rate_cfg = os.environ.get("MCP_INDIA_STACK_RATE_LIMIT", "60/60").strip()
        try:
            _rate_parts = _rate_cfg.split("/")
            _rate_max = int(_rate_parts[0])
            _rate_window = int(_rate_parts[1]) if len(_rate_parts) > 1 else 60
        except (ValueError, IndexError):
            _rate_max, _rate_window = 60, 60

        sse_app_instance.add_middleware(
            _RateLimitMiddleware,
            max_requests=_rate_max,
            window_seconds=_rate_window,
        )

        # --- Auth gate (Bearer token middleware) ---
        class _BearerAuthMiddleware(BaseHTTPMiddleware):
            def __init__(self, app: Any, api_key: str) -> None:
                super().__init__(app)
                self.api_key = api_key

            async def dispatch(self, request: Request, call_next: Any) -> Any:
                auth = request.headers.get("Authorization", "")
                if not auth.startswith("Bearer ") or auth[7:] != self.api_key:
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)
                response: Any = await call_next(request)
                return response

        _api_key = os.environ.get("MCP_INDIA_STACK_API_KEY", "").strip()
        if _api_key:
            sse_app_instance.add_middleware(_BearerAuthMiddleware, api_key=_api_key)
        else:
            sse_logger.warning(
                "MCP_INDIA_STACK_API_KEY is not set — "
                "SSE server is publicly reachable with no authentication"
            )

        for route in sse_app_instance.router.routes:
            if hasattr(route, "path") and route.path in ("/sse", ""):
                route.methods = {"GET", "POST"}  # type: ignore
            if hasattr(route, "path") and route.path in ("/messages", "/messages/"):
                route.methods = {"GET", "POST"}  # type: ignore

        uvicorn.run(sse_app_instance, host=args.host, port=port)
    else:
        mcp.run(transport="stdio")
