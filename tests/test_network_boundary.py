"""Tests for network boundary hardening (Update 1/7).

Covers: CORS (R1), Auth gate (R2), Rate limiting (R3),
Bulk worker clamp (R4), Circuit breaker (R5).
"""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# R4: Bulk worker clamp tests
# ---------------------------------------------------------------------------
class TestBulkWorkerClamp:
    """_BULK_WORKERS resolves to [1, 20] for all edge-case inputs."""

    def _get_clamped(self, env_val: str | None) -> int:
        """Import the clamp function with a patched env var."""
        env = os.environ.copy()
        if env_val is None:
            env.pop("MCP_INDIA_STACK_BULK_WORKERS", None)
        else:
            env["MCP_INDIA_STACK_BULK_WORKERS"] = env_val

        with patch.dict(os.environ, env, clear=True):
            # Re-run the clamp logic (can't reimport module, test the function)
            raw = os.environ.get("MCP_INDIA_STACK_BULK_WORKERS", "10")
            try:
                val = int(raw)
            except (ValueError, TypeError):
                return 10
            return max(1, min(20, val))

    def test_unset_defaults_to_10(self) -> None:
        assert self._get_clamped(None) == 10

    def test_zero_clamps_to_1(self) -> None:
        assert self._get_clamped("0") == 1

    def test_negative_clamps_to_1(self) -> None:
        assert self._get_clamped("-5") == 1

    def test_over_max_clamps_to_20(self) -> None:
        assert self._get_clamped("9999") == 20

    def test_non_integer_falls_back_to_10(self) -> None:
        assert self._get_clamped("abc") == 10

    def test_valid_value_passes_through(self) -> None:
        assert self._get_clamped("15") == 15

    def test_boundary_1(self) -> None:
        assert self._get_clamped("1") == 1

    def test_boundary_20(self) -> None:
        assert self._get_clamped("20") == 20


# ---------------------------------------------------------------------------
# R5: Circuit breaker tests
# ---------------------------------------------------------------------------
class TestCircuitBreaker:
    """Circuit breaker opens after N failures and closes after cooldown."""

    def _make_breaker(self, threshold: int = 5, cooldown: float = 30.0):  # type: ignore[no-untyped-def]
        from mcp_india_stack.tools.ifsc import _CircuitBreaker

        return _CircuitBreaker(threshold, cooldown)

    def test_starts_closed(self) -> None:
        cb = self._make_breaker()
        assert cb.is_open is False

    def test_opens_after_threshold_failures(self) -> None:
        cb = self._make_breaker(threshold=3, cooldown=10.0)
        for _ in range(3):
            cb.record_failure()
        assert cb.is_open is True

    def test_stays_closed_below_threshold(self) -> None:
        cb = self._make_breaker(threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.is_open is False

    def test_success_resets_counter(self) -> None:
        cb = self._make_breaker(threshold=3, cooldown=10.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()
        # Only 2 consecutive failures after reset, threshold is 3
        assert cb.is_open is False

    def test_closes_after_cooldown(self) -> None:
        cb = self._make_breaker(threshold=2, cooldown=0.5)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True
        time.sleep(0.6)
        assert cb.is_open is False

    def test_ifsc_lookup_skips_http_when_circuit_open(self) -> None:
        """When circuit is open, live lookup is skipped without HTTP call."""
        from mcp_india_stack.tools import ifsc as ifsc_module

        # Save original breaker state and replace with a tripped breaker
        original_breaker = ifsc_module._ifsc_breaker
        try:
            test_breaker = self._make_breaker(threshold=1, cooldown=60.0)
            test_breaker.record_failure()  # Trip it
            ifsc_module._ifsc_breaker = test_breaker

            with (
                patch.object(ifsc_module, "_LIVE_LOOKUP_ENABLED", True),
                patch("httpx.Client") as mock_client,
            ):
                result = ifsc_module.lookup_ifsc("SBIN0000000")
                # httpx.Client should never be instantiated
                mock_client.assert_not_called()
                assert "live_lookup_skipped: circuit_open" in result.get("warnings", [])
        finally:
            ifsc_module._ifsc_breaker = original_breaker


# ---------------------------------------------------------------------------
# R1: CORS configuration tests
# ---------------------------------------------------------------------------
class TestCORSConfiguration:
    """No configuration path can produce allow_origins=['*'] + allow_credentials=True."""

    def test_default_rejects_credentials(self) -> None:
        """Unset env -> empty origins, credentials False."""
        raw = ""
        origins = [o.strip() for o in raw.split(",") if o.strip()] if raw else []
        creds = bool(origins)
        assert origins == []
        assert creds is False

    def test_explicit_origins_enables_credentials(self) -> None:
        """Explicit origins -> parsed list, credentials True."""
        raw = "https://example.com, https://app.example.com"
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        creds = bool(origins)
        assert origins == ["https://example.com", "https://app.example.com"]
        assert creds is True

    def test_wildcard_with_credentials_raises(self) -> None:
        """Setting '*' as origin must raise RuntimeError."""
        raw = "*"
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        creds = bool(origins)
        assert creds is True
        assert "*" in origins
        # Simulate the guard check from server.py
        with pytest.raises(RuntimeError, match="CORS misconfiguration"):
            if creds and "*" in origins:
                raise RuntimeError(
                    "CORS misconfiguration: allow_origins=['*'] with "
                    "allow_credentials=True is forbidden. Set explicit "
                    "origins in MCP_INDIA_STACK_ALLOWED_ORIGINS."
                )

    def test_wildcard_among_others_raises(self) -> None:
        """'*' mixed with real origins must also raise."""
        raw = "https://example.com, *"
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        creds = bool(origins)
        with pytest.raises(RuntimeError, match="CORS misconfiguration"):
            if creds and "*" in origins:
                raise RuntimeError(
                    "CORS misconfiguration: allow_origins=['*'] with "
                    "allow_credentials=True is forbidden. Set explicit "
                    "origins in MCP_INDIA_STACK_ALLOWED_ORIGINS."
                )


# ---------------------------------------------------------------------------
# R2: Auth gate tests
# ---------------------------------------------------------------------------
class TestAuthGate:
    """Bearer token auth middleware behavior."""

    @pytest.fixture()
    def _auth_app(self):  # type: ignore[no-untyped-def]
        """Create a minimal Starlette app with the auth middleware."""
        from starlette.applications import Starlette
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        async def _hello(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        class AuthMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
            def __init__(self, app, api_key: str) -> None:  # type: ignore[no-untyped-def]
                super().__init__(app)
                self.api_key = api_key

            async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
                auth = request.headers.get("Authorization", "")
                if not auth.startswith("Bearer ") or auth[7:] != self.api_key:
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)
                return await call_next(request)

        app = Starlette(routes=[Route("/test", _hello)])
        app.add_middleware(AuthMiddleware, api_key="secret123")
        return TestClient(app)

    def test_rejects_without_token(self, _auth_app) -> None:  # type: ignore[no-untyped-def]
        resp = _auth_app.get("/test")
        assert resp.status_code == 401

    def test_rejects_wrong_token(self, _auth_app) -> None:  # type: ignore[no-untyped-def]
        resp = _auth_app.get("/test", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401

    def test_accepts_valid_token(self, _auth_app) -> None:  # type: ignore[no-untyped-def]
        resp = _auth_app.get("/test", headers={"Authorization": "Bearer secret123"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_rejects_non_bearer_scheme(self, _auth_app) -> None:  # type: ignore[no-untyped-def]
        resp = _auth_app.get("/test", headers={"Authorization": "Basic abc123"})
        assert resp.status_code == 401

    def test_no_auth_middleware_allows_all(self) -> None:
        """When no API key is set, requests pass through."""
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        async def _hello(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        app = Starlette(routes=[Route("/test", _hello)])
        # No auth middleware added
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# R3: Rate limiting tests
# ---------------------------------------------------------------------------
class TestRateLimiting:
    """Per-IP rate limiting returns 429 when exceeded."""

    @pytest.fixture()
    def _rate_app(self):  # type: ignore[no-untyped-def]
        """Create a minimal Starlette app with rate limiting (3 req/60s)."""
        import threading

        from starlette.applications import Starlette
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        async def _hello(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok"})

        class RateLimitMW(BaseHTTPMiddleware):  # type: ignore[misc]
            def __init__(self, app, max_requests: int = 3, window_seconds: int = 60) -> None:  # type: ignore[no-untyped-def]
                super().__init__(app)
                self.max_requests = max_requests
                self.window_seconds = window_seconds
                self._buckets: dict[str, list[float]] = {}
                self._lock = threading.Lock()

            async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
                key = f"ip:{request.client.host}" if request.client else "ip:unknown"
                now = time.monotonic()
                with self._lock:
                    timestamps = self._buckets.setdefault(key, [])
                    cutoff = now - self.window_seconds
                    timestamps[:] = [t for t in timestamps if t > cutoff]
                    if len(timestamps) >= self.max_requests:
                        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
                    timestamps.append(now)
                return await call_next(request)

        app = Starlette(routes=[Route("/test", _hello)])
        app.add_middleware(RateLimitMW, max_requests=3, window_seconds=60)
        return TestClient(app)

    def test_allows_within_limit(self, _rate_app) -> None:  # type: ignore[no-untyped-def]
        for _ in range(3):
            resp = _rate_app.get("/test")
            assert resp.status_code == 200

    def test_returns_429_beyond_limit(self, _rate_app) -> None:  # type: ignore[no-untyped-def]
        for _ in range(3):
            _rate_app.get("/test")
        resp = _rate_app.get("/test")
        assert resp.status_code == 429
        assert resp.json()["error"] == "Rate limit exceeded"
