"""FastMCP server entry point for mcp-india-stack.

This is a thin entry point that:
- Imports the shared FastMCP instance from app.py
- Triggers tool registration via the registrations/ package
- Defines server-level resources, prompt templates, and the CLI runner
- Wires CORS, auth, and rate-limit middleware for SSE transport
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
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
                "version": "0.7.0",
                "date": "2026-10-29",
                "changes": [
                    "Offline-only bundled datasets; removed runtime CDN downloads and caching",
                    "Hardened CI security gates (Bandit, pip-audit, lock drift, smoke test)",
                    "Added 20 architectural regression guards (G01-G20)",
                    "Extracted 9 inline tools to tools/ package and achieved 100% core parity",
                ],
            },
            {
                "version": "0.6.9",
                "date": "2026-10-02",
                "changes": [
                    "Update 6/7: Dependency reproducibility",
                    "Added requirements.txt lockfile for deterministic CI builds",
                    "Pinned upper bounds for behavior-sensitive dependencies (polars, yfinance)",
                    "Isolated yfinance behind a clean provider abstraction",
                ],
            },
            {
                "version": "0.6.7",
                "date": "2026-10-02",
                "changes": [
                    "Update 5/7: Decomposed server.py by domain",
                    "Extracted 7 registration modules (kyc, tax, banking, finance, etc)",
                    "Extracted inline tools (esic_code, epf_code, digilocker, etc) to tools dir",
                ],
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="mcp-india-stack MCP server")
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help=argparse.SUPPRESS,
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
        default="127.0.0.1",
        help="Host to bind to for SSE transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to for SSE transport (default: from $PORT or 8000)",
    )
    args = parser.parse_args()

    if args.refresh_all:
        sys.stderr.write("dataset refresh was removed; upgrade the package to receive new data\n")
        sys.exit(2)

    if args.transport == "sse":
        import uvicorn
        from mcp.server.transport_security import TransportSecuritySettings
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.middleware.cors import CORSMiddleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        sse_logger = logging.getLogger("mcp_india_stack")

        effective_host = args.host
        if effective_host == "127.0.0.1" and os.environ.get("RENDER"):
            effective_host = str(ipaddress.IPv4Address(0))

        port = args.port
        if port is None:
            port = int(os.environ.get("PORT", "8000"))

        # --- D6: Fail-closed startup checks (before any server setup or uvicorn.run) ---
        _api_key = os.environ.get("MCP_INDIA_STACK_API_KEY", "").strip()
        if _api_key and len(_api_key) < 32:
            sys.stderr.write(
                "MCP_INDIA_STACK_API_KEY must be at least 32 characters. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"\n'
            )
            sys.exit(1)

        is_loopback = False
        try:
            is_loopback = ipaddress.ip_address(effective_host).is_loopback or effective_host in (
                "127.0.0.1",
                "localhost",
                "::1",
            )
        except ValueError:
            is_loopback = effective_host == "localhost"

        if not is_loopback and not _api_key:
            _allow_unauth = os.environ.get(
                "MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK", ""
            ).strip()
            if _allow_unauth != "1":
                sys.stderr.write(
                    "Refusing to bind to non-loopback host without authentication. "
                    "Set MCP_INDIA_STACK_API_KEY or opt in with "
                    "MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK=1\n"
                )
                sys.exit(1)
            sse_logger.warning(
                "Running unauthenticated on non-loopback host %s because "
                "MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK=1",
                effective_host,
            )

        _raw_hosts = os.environ.get("MCP_INDIA_STACK_ALLOWED_HOSTS", "").strip()
        _render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
        if not is_loopback and not _raw_hosts and not _render_host:
            sse_logger.warning(
                "Non-loopback host %s without MCP_INDIA_STACK_ALLOWED_HOSTS or "
                "RENDER_EXTERNAL_HOSTNAME; requests will be rejected with 421",
                effective_host,
            )

        # --- D5: Transport security settings ---
        _configured_hosts = (
            [h.strip() for h in _raw_hosts.split(",") if h.strip()] if _raw_hosts else []
        )
        for h in _configured_hosts:
            if "://" in h or "/" in h or any(c.isspace() for c in h):
                sys.stderr.write(
                    f"Invalid entry in MCP_INDIA_STACK_ALLOWED_HOSTS: {h!r} "
                    "(must not contain scheme, path, or whitespace)\n"
                )
                sys.exit(1)

        allowed_hosts_set = {
            "127.0.0.1:*",
            "localhost:*",
            "[::1]:*",
            "127.0.0.1",
            "localhost",
            "[::1]",
        }
        for h in _configured_hosts:
            if ":" in h or "*" in h:
                allowed_hosts_set.add(h)
            else:
                allowed_hosts_set.add(h)
                allowed_hosts_set.add(f"{h}:*")

        if _render_host:
            if ":" in _render_host or "*" in _render_host:
                allowed_hosts_set.add(_render_host)
            else:
                allowed_hosts_set.add(_render_host)
                allowed_hosts_set.add(f"{_render_host}:*")

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

        loopback_origins = [
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
        ]
        transport_origins = loopback_origins + _allowed_origins

        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=sorted(allowed_hosts_set),
            allowed_origins=transport_origins,
        )

        sse_app_instance = mcp.sse_app()

        # --- D3: Rate limiting middleware (inner middleware) ---
        class _RateLimitMiddleware(BaseHTTPMiddleware):
            """Rate-limits validated requests using a bounded in-memory sliding window."""

            def __init__(
                self,
                app: Any,
                max_requests: int = 60,
                window_seconds: int = 60,
                max_entries: int = 10000,
                rate_key: str | None = None,
            ) -> None:
                super().__init__(app)
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self.max_entries = max_entries
                self._rate_key = rate_key
                self._buckets: dict[str, list[float]] = {}
                self._lock = threading.Lock()

            def _get_key(self, request: Request) -> str:
                if self._rate_key is not None:
                    return self._rate_key
                client_host = request.client.host if request.client else "unknown"
                return f"ip:{client_host}"

            async def dispatch(self, request: Request, call_next: Any) -> Any:
                if request.url.path in ("/health", "/health/", "/"):
                    return await call_next(request)
                key = self._get_key(request)
                now = time.monotonic()
                with self._lock:
                    if key not in self._buckets and len(self._buckets) >= self.max_entries:
                        # Bounded store: evict oldest entry
                        oldest_key = next(iter(self._buckets))
                        del self._buckets[oldest_key]
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

        # --- D2: Auth gate (Bearer token middleware with failure throttle) ---
        class _BearerAuthMiddleware(BaseHTTPMiddleware):
            """Authenticates requests via Bearer token and throttles failed authentication."""

            def __init__(
                self,
                app: Any,
                api_key: str,
                fail_limit: int = 10,
                max_entries: int = 10000,
            ) -> None:
                super().__init__(app)
                self.api_key = api_key
                self.fail_limit = fail_limit
                self.max_entries = max_entries
                self._fail_store: dict[str, list[float]] = {}
                self._lock = threading.Lock()

            async def dispatch(self, request: Request, call_next: Any) -> Any:
                if request.method == "OPTIONS" or request.url.path in (
                    "/health",
                    "/health/",
                    "/",
                ):
                    return await call_next(request)
                auth = request.headers.get("Authorization", "")
                valid = False
                if auth.startswith("Bearer "):
                    token_bytes = auth[7:].encode("utf-8", errors="replace")
                    key_bytes = self.api_key.encode("utf-8")
                    token_hash = hashlib.sha256(token_bytes).digest()
                    expected_hash = hashlib.sha256(key_bytes).digest()
                    if hmac.compare_digest(token_hash, expected_hash):
                        valid = True

                if valid:
                    # Valid token passes directly; valid requests never touch failure store
                    return await call_next(request)

                # Missing or invalid token: count as a failure keyed by client host
                client_host = request.client.host if request.client else "unknown"
                now = time.monotonic()
                with self._lock:
                    if (
                        client_host not in self._fail_store
                        and len(self._fail_store) >= self.max_entries
                    ):
                        oldest_key = next(iter(self._fail_store))
                        del self._fail_store[oldest_key]
                    failures = self._fail_store.setdefault(client_host, [])
                    cutoff = now - 60.0
                    failures[:] = [t for t in failures if t > cutoff]
                    if len(failures) >= self.fail_limit:
                        retry_after = max(1, int(60.0 - (now - failures[0])))
                        return JSONResponse(
                            {"error": "Too many failed authentication attempts"},
                            status_code=429,
                            headers={"Retry-After": str(retry_after)},
                        )
                    failures.append(now)

                return JSONResponse({"error": "Unauthorized"}, status_code=401)

        _raw_fail_limit = os.environ.get("MCP_INDIA_STACK_AUTH_FAIL_LIMIT", "10").strip()
        try:
            _fail_limit = int(_raw_fail_limit)
            if _fail_limit < 1:
                _fail_limit = 10
        except ValueError:
            _fail_limit = 10

        # --- D1: Middleware order, outermost to innermost: CORS, Auth, RateLimit ---
        # Starlette wraps middlewares in reverse addition order: the LAST added call is outermost.
        # RateLimit keys on caller-supplied tokens, so it must sit inside Auth.
        _rate_key = (
            "key:" + hashlib.sha256(_api_key.encode("utf-8")).hexdigest()[:16] if _api_key else None
        )
        sse_app_instance.add_middleware(
            _RateLimitMiddleware,
            max_requests=_rate_max,
            window_seconds=_rate_window,
            rate_key=_rate_key,
        )

        if _api_key:
            sse_app_instance.add_middleware(
                _BearerAuthMiddleware,
                api_key=_api_key,
                fail_limit=_fail_limit,
            )
        else:
            sse_logger.warning(
                "MCP_INDIA_STACK_API_KEY is not set — "
                "SSE server is publicly reachable with no authentication"
            )

        sse_app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=_allowed_origins,
            allow_credentials=_allow_creds,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

        async def _health_check(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok", "version": __version__})

        async def _root_check(request: Request) -> JSONResponse:
            return JSONResponse(
                {"status": "ok", "service": "mcp-india-stack", "version": __version__}
            )

        sse_app_instance.add_route("/health", _health_check, methods=["GET"])
        sse_app_instance.add_route("/health/", _health_check, methods=["GET"])
        sse_app_instance.add_route("/", _root_check, methods=["GET"])

        for route in sse_app_instance.router.routes:
            if hasattr(route, "path") and route.path in ("/sse", ""):
                route.methods = {"GET", "POST"}  # type: ignore
            if hasattr(route, "path") and route.path in ("/messages", "/messages/"):
                route.methods = {"GET", "POST"}  # type: ignore

        sys.stdout.write(
            f"Starting mcp-india-stack v{__version__} on {effective_host}:{port} (transport=sse)\n"
        )
        sys.stdout.flush()

        uvicorn.run(sse_app_instance, host=effective_host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
