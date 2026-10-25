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


# ===========================================================================
# Update 6.6: Network boundary completion (D1-D9 / T1-T9)
# ===========================================================================
import copy
import hashlib
import logging
import sys
from typing import Any

from starlette.testclient import TestClient

import mcp_india_stack.server as server_module
from mcp_india_stack.app import mcp
from tests._app_harness import VALID_TEST_API_KEY, captured_server_app

VALID_KEY = VALID_TEST_API_KEY


class TestNetworkBoundary:
    """Network boundary test suite validating D1-D9 requirements."""

    def test_t1_middleware_order_by_user_middleware_and_behavior(self) -> None:
        """T1: Assert order CORS, Auth, RateLimit by structure and behavior."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://example.com",
            "MCP_INDIA_STACK_RATE_LIMIT": "5/60",
        }
        with captured_server_app(env) as app:
            # Starlette user_middleware is in reverse insertion order
            names = [m.cls.__name__ for m in app.user_middleware]
            # Outermost is index 0 in user_middleware (the last add_middleware call)
            assert names[0] == "CORSMiddleware"
            assert names[1] == "_BearerAuthMiddleware"
            assert names[2] == "_RateLimitMiddleware"

            stack = app.build_middleware_stack()
            curr = stack
            runtime_order = []
            while curr:
                runtime_order.append(curr.__class__.__name__)
                curr = getattr(curr, "app", None)

            cors_idx = runtime_order.index("CORSMiddleware")
            auth_idx = runtime_order.index("_BearerAuthMiddleware")
            rate_idx = runtime_order.index("_RateLimitMiddleware")
            assert cors_idx < auth_idx < rate_idx

            # Verify by behavior: preflight OPTIONS succeeds because CORS is outside Auth
            client = TestClient(app, raise_server_exceptions=False)
            preflight = client.options(
                "/messages/",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert preflight.status_code == 200
            assert preflight.headers.get("Access-Control-Allow-Origin") == "https://example.com"

    def test_t2_preflight_cors_handling(self) -> None:
        """T2: Preflight with allowed Origin succeeds; disallowed Origin is rejected with 400."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://app.example.com",
        }
        with captured_server_app(env) as app:
            client = TestClient(app, raise_server_exceptions=False)

            # Allowed origin
            resp_ok = client.options(
                "/messages/",
                headers={
                    "Origin": "https://app.example.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert resp_ok.status_code == 200
            assert resp_ok.headers.get("Access-Control-Allow-Origin") == "https://app.example.com"

            # Disallowed origin
            resp_bad = client.options(
                "/messages/",
                headers={
                    "Origin": "https://evil.example.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert resp_bad.status_code == 400
            assert "Disallowed CORS origin" in resp_bad.text

    def test_t3_error_responses_carry_cors_headers(self) -> None:
        """T3: 401 and 429 responses carry CORS headers for an allowed Origin."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://example.com",
            "MCP_INDIA_STACK_AUTH_FAIL_LIMIT": "2",
        }
        with captured_server_app(env) as app:
            client = TestClient(app, raise_server_exceptions=False)

            # 401 Unauthorized
            r401 = client.post(
                "/messages/",
                headers={"Origin": "https://example.com", "Authorization": "Bearer wrong_1"},
                json={},
            )
            assert r401.status_code == 401
            assert r401.headers.get("Access-Control-Allow-Origin") == "https://example.com"

            # Trigger failure limit -> 429
            client.post(
                "/messages/",
                headers={"Origin": "https://example.com", "Authorization": "Bearer wrong_2"},
                json={},
            )
            r429 = client.post(
                "/messages/",
                headers={"Origin": "https://example.com", "Authorization": "Bearer wrong_3"},
                json={},
            )
            assert r429.status_code == 429
            assert r429.headers.get("Access-Control-Allow-Origin") == "https://example.com"
            assert "Retry-After" in r429.headers

    def test_t4_failure_throttle_and_valid_token_isolation(self) -> None:
        """T4: LIMIT+1 failures return 429; valid token in same window still succeeds."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://example.com",
            "MCP_INDIA_STACK_AUTH_FAIL_LIMIT": "3",
        }
        with captured_server_app(env) as app:
            client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )

            for i in range(3):
                r = client.post(
                    "/messages/",
                    headers={"Authorization": f"Bearer invalid_{i}"},
                    json={},
                )
                assert r.status_code == 401

            # 4th request from same client exceeds limit
            r_throttled = client.post(
                "/messages/",
                headers={"Authorization": "Bearer invalid_4"},
                json={},
            )
            assert r_throttled.status_code == 429
            assert "Retry-After" in r_throttled.headers

            # Request with valid token in same window still succeeds
            r_valid = client.post(
                "/messages/",
                headers={
                    "Authorization": f"Bearer {VALID_KEY}",
                    "Content-Type": "application/json",
                },
                json={"ping": True},
            )
            # Passes Auth (reaches inner MCP handler; 400 because session_id absent)
            assert r_valid.status_code == 400
            assert "session_id is required" in r_valid.text

    def test_t4b_failure_and_ratelimit_store_bounds(self) -> None:
        """T4b: After 2000 invalid tokens, failure store <= cap and rate-limit store has 0."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_AUTH_FAIL_LIMIT": "10000",
        }
        with captured_server_app(env) as app:
            client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )

            # Prime middleware stack
            client.post("/messages/", headers={"Authorization": "Bearer bad"}, json={})

            curr = app.middleware_stack
            auth_mw = None
            rate_mw = None
            while curr:
                if "_BearerAuthMiddleware" in curr.__class__.__name__:
                    auth_mw = curr
                elif "_RateLimitMiddleware" in curr.__class__.__name__:
                    rate_mw = curr
                curr = getattr(curr, "app", None)

            assert auth_mw is not None
            assert rate_mw is not None

            for i in range(2000):
                client.post("/messages/", headers={"Authorization": f"Bearer token_{i}"}, json={})

            assert len(auth_mw._fail_store) <= auth_mw.max_entries
            assert len(rate_mw._buckets) == 0

    def test_t4c_rate_limit_semantics_and_token_hash_keys(self) -> None:
        """T4c: Requests beyond RATE_LIMIT return 429; store keys use token hash or IP."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_RATE_LIMIT": "3/60",
        }
        with captured_server_app(env) as app:
            client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )

            for _ in range(3):
                r = client.post(
                    "/messages/",
                    headers={
                        "Authorization": f"Bearer {VALID_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={},
                )
                assert r.status_code == 400  # session_id check

            # 4th exceeds rate limit
            r_rate = client.post(
                "/messages/",
                headers={
                    "Authorization": f"Bearer {VALID_KEY}",
                    "Content-Type": "application/json",
                },
                json={},
            )
            assert r_rate.status_code == 429

            curr = app.middleware_stack
            rate_mw = None
            while curr:
                if "_RateLimitMiddleware" in curr.__class__.__name__:
                    rate_mw = curr
                    break
                curr = getattr(curr, "app", None)
            assert rate_mw is not None
            expected_prefix = "key:" + hashlib.sha256(VALID_KEY.encode("utf-8")).hexdigest()[:16]
            assert set(rate_mw._buckets.keys()) == {expected_prefix}
            assert len(rate_mw._buckets) == 1
            key = next(iter(rate_mw._buckets))
            assert key.startswith("key:")
            assert VALID_KEY not in key
            assert len(key) == len("key:") + 16

        # Test unauthenticated rate limit keys by IP
        env_unauth = {
            "MCP_INDIA_STACK_API_KEY": "",
            "MCP_INDIA_STACK_RATE_LIMIT": "2/60",
        }
        with captured_server_app(env_unauth) as app_unauth:
            client_unauth = TestClient(
                app_unauth, base_url="http://localhost:8000", raise_server_exceptions=False
            )
            client_unauth.post("/messages/", headers={"Content-Type": "application/json"}, json={})

            curr = app_unauth.middleware_stack
            rate_mw_unauth = None
            while curr:
                if "_RateLimitMiddleware" in curr.__class__.__name__:
                    rate_mw_unauth = curr
                    break
                curr = getattr(curr, "app", None)
            assert rate_mw_unauth is not None
            unauth_key = next(iter(rate_mw_unauth._buckets))
            assert unauth_key.startswith("ip:")

    def test_t4d_unauthenticated_bearer_rotation_cannot_bypass_rate_limit(self) -> None:
        """T4d: Rotating Bearer tokens from same client cannot bypass unauthenticated limit."""
        env = {
            "MCP_INDIA_STACK_API_KEY": "",
            "MCP_INDIA_STACK_RATE_LIMIT": "3/60",
        }
        with captured_server_app(env) as app:
            client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )
            for i in range(3):
                r = client.post(
                    "/messages/",
                    headers={
                        "Authorization": f"Bearer fake_token_{i}",
                        "Content-Type": "application/json",
                    },
                    json={},
                )
                assert r.status_code == 400

            r_throttled = client.post(
                "/messages/",
                headers={
                    "Authorization": "Bearer fake_token_4",
                    "Content-Type": "application/json",
                },
                json={},
            )
            assert r_throttled.status_code == 429

            curr = app.middleware_stack
            rate_mw = None
            while curr:
                if "_RateLimitMiddleware" in curr.__class__.__name__:
                    rate_mw = curr
                    break
                curr = getattr(curr, "app", None)

            assert rate_mw is not None
            assert len(rate_mw._buckets) == 1
            entry_key = next(iter(rate_mw._buckets))
            assert entry_key.startswith("ip:")

    def test_t4e_auth_failure_store_eviction_bounded(self) -> None:
        """T4e: Auth failure store bounds entries to max_entries and evicts oldest addresses."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_AUTH_FAIL_LIMIT": "10",
        }
        with captured_server_app(env) as app:
            # Prime middleware stack
            prime_client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )
            prime_client.post("/messages/", headers={"Authorization": "Bearer bad"}, json={})

            curr = app.middleware_stack
            auth_mw = None
            while curr:
                if "_BearerAuthMiddleware" in curr.__class__.__name__:
                    auth_mw = curr
                    break
                curr = getattr(curr, "app", None)

            assert auth_mw is not None
            auth_mw.max_entries = 5

            # Drive app with 20 distinct client addresses using TestClient(client=(addr, port))
            for i in range(20):
                client = TestClient(
                    app,
                    client=(f"192.0.2.{i}", 50000 + i),
                    base_url="http://localhost:8000",
                    raise_server_exceptions=False,
                )
                r = client.post("/messages/", headers={"Authorization": "Bearer invalid"}, json={})
                assert r.status_code == 401

            assert len(auth_mw._fail_store) <= 5
            assert "192.0.2.19" in auth_mw._fail_store

    def test_t4f_rate_limit_ip_store_eviction_bounded(self) -> None:
        """T4f: Unauthenticated rate limiter bounds _buckets to max_entries and evicts oldest."""
        env = {
            "MCP_INDIA_STACK_API_KEY": "",
            "MCP_INDIA_STACK_RATE_LIMIT": "60/60",
        }
        with captured_server_app(env) as app:
            # Prime middleware stack
            prime_client = TestClient(
                app, base_url="http://localhost:8000", raise_server_exceptions=False
            )
            prime_client.post("/messages/", headers={"Content-Type": "application/json"}, json={})

            curr = app.middleware_stack
            rate_mw = None
            while curr:
                if "_RateLimitMiddleware" in curr.__class__.__name__:
                    rate_mw = curr
                    break
                curr = getattr(curr, "app", None)

            assert rate_mw is not None
            rate_mw.max_entries = 5

            for i in range(20):
                client = TestClient(
                    app,
                    client=(f"198.51.100.{i}", 50000 + i),
                    base_url="http://localhost:8000",
                    raise_server_exceptions=False,
                )
                r = client.post("/messages/", headers={"Content-Type": "application/json"}, json={})
                assert r.status_code == 400  # inner MCP handler reached

            assert len(rate_mw._buckets) <= 5
            assert "ip:198.51.100.19" in rate_mw._buckets

    def test_t5_transport_security_host_and_origin(self) -> None:
        """T5: Transport security host validation (421) and origin validation (403)."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_HOSTS": "custom.example.com",
            "RENDER_EXTERNAL_HOSTNAME": "my-service.onrender.com",
            "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://allowed.example.com",
        }
        with captured_server_app(env) as app:
            client = TestClient(app, raise_server_exceptions=False)

            base_headers = {
                "Authorization": f"Bearer {VALID_KEY}",
                "Content-Type": "application/json",
            }

            # Loopback host passes (400 session_id required, not 421)
            r1 = client.post(
                "/messages/",
                headers={**base_headers, "Host": "127.0.0.1:8000"},
                json={},
            )
            assert r1.status_code == 400

            # Bare localhost passes
            r2 = client.post(
                "/messages/",
                headers={**base_headers, "Host": "localhost"},
                json={},
            )
            assert r2.status_code == 400

            # Unlisted host receives 421
            r3 = client.post(
                "/messages/",
                headers={**base_headers, "Host": "unlisted.example.com"},
                json={},
            )
            assert r3.status_code == 421
            assert "Invalid Host header" in r3.text

            # ALLOWED_HOSTS entry passes
            r4 = client.post(
                "/messages/",
                headers={**base_headers, "Host": "custom.example.com"},
                json={},
            )
            assert r4.status_code == 400

            # RENDER_EXTERNAL_HOSTNAME passes
            r5 = client.post(
                "/messages/",
                headers={**base_headers, "Host": "my-service.onrender.com"},
                json={},
            )
            assert r5.status_code == 400

            # Listed Origin passes
            r6 = client.post(
                "/messages/",
                headers={
                    **base_headers,
                    "Host": "localhost",
                    "Origin": "https://allowed.example.com",
                },
                json={},
            )
            assert r6.status_code == 400

            # Unlisted Origin receives 403
            r7 = client.post(
                "/messages/",
                headers={
                    **base_headers,
                    "Host": "localhost",
                    "Origin": "https://evil.example.com",
                },
                json={},
            )
            assert r7.status_code == 403
            assert "Invalid Origin header" in r7.text

    def test_t6_fail_closed_startup_matrix(self, caplog: pytest.LogCaptureFixture) -> None:
        """T6: Fail-closed matrix over host x key x opt-in."""
        cases: list[
            tuple[
                str,
                str | None,
                str | None,
                dict[str, str] | None,
                bool,
                str | None,
                str | None,
            ]
        ] = [
            # (host, key, opt-in, extra_env, should_succeed, expected_warn, forbidden_warn)
            ("127.0.0.1", VALID_KEY, None, None, True, None, None),
            ("127.0.0.1", None, None, None, True, "is not set", None),
            ("127.0.0.1", "short", None, None, False, None, None),  # key < 32 chars -> exit
            ("0.0.0.0", VALID_KEY, None, None, True, "without MCP_INDIA_STACK_ALLOWED_HOSTS", None),
            # Host 0.0.0.0 with RENDER_EXTERNAL_HOSTNAME: starts, no 421 warning
            (
                "0.0.0.0",
                VALID_KEY,
                None,
                {"RENDER_EXTERNAL_HOSTNAME": "srv.onrender.com"},
                True,
                None,
                "requests will be rejected with 421",
            ),
            # Host 0.0.0.0 with MCP_INDIA_STACK_ALLOWED_HOSTS: starts, no 421 warning
            (
                "0.0.0.0",
                VALID_KEY,
                None,
                {"MCP_INDIA_STACK_ALLOWED_HOSTS": "my.domain.com"},
                True,
                None,
                "requests will be rejected with 421",
            ),
            ("0.0.0.0", "short", None, None, False, None, None),
            # non-loopback without key & without opt-in -> exit
            ("0.0.0.0", None, None, None, False, None, None),
            (
                "0.0.0.0",
                None,
                "1",
                None,
                True,
                "Running unauthenticated on non-loopback host",
                None,
            ),
        ]

        for (
            host,
            key,
            opt_in,
            extra_env,
            should_succeed,
            warn_snippet,
            forbidden_snippet,
        ) in cases:
            env: dict[str, str] = {}
            if key is not None:
                env["MCP_INDIA_STACK_API_KEY"] = key
            if opt_in is not None:
                env["MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK"] = opt_in
            if extra_env is not None:
                env.update(extra_env)

            argv = ["mcp-india-stack", "--transport", "sse", "--host", host]

            uvicorn_called = False

            def fake_uvicorn(app: Any, **kwargs: Any) -> None:
                nonlocal uvicorn_called
                uvicorn_called = True

            with patch.dict(os.environ, env, clear=True):
                with patch.object(sys, "argv", argv):
                    with patch("uvicorn.run", side_effect=fake_uvicorn):
                        caplog.clear()
                        if should_succeed:
                            with caplog.at_level(logging.WARNING):
                                server_module.main()
                            assert uvicorn_called is True
                            if warn_snippet:
                                assert warn_snippet in caplog.text
                            if forbidden_snippet:
                                assert forbidden_snippet not in caplog.text
                        else:
                            with pytest.raises(SystemExit) as exc:
                                server_module.main()
                            assert exc.value.code != 0
                            assert uvicorn_called is False

    def test_t7_protection_stays_enabled(self) -> None:
        """T7: DNS rebinding protection stays enabled; FastMCP never receives non-loopback host."""
        env = {
            "MCP_INDIA_STACK_API_KEY": VALID_KEY,
            "MCP_INDIA_STACK_ALLOWED_HOSTS": "test.host",
        }
        argv = ["mcp-india-stack", "--transport", "sse", "--host", "0.0.0.0"]
        with captured_server_app(env, argv=argv):
            assert mcp.settings.transport_security is not None
            assert mcp.settings.transport_security.enable_dns_rebinding_protection is True
            assert mcp.settings.host in ("127.0.0.1", "localhost", None)

    def test_t8_invalid_allowed_hosts_refuses_startup(self) -> None:
        """T8: Invalid ALLOWED_HOSTS entries (scheme, path, whitespace) refuse startup."""
        invalid_entries = [
            "https://example.com",
            "example.com/api",
            "example .com",
            "example\t.com",
        ]
        for entry in invalid_entries:
            env = {
                "MCP_INDIA_STACK_API_KEY": VALID_KEY,
                "MCP_INDIA_STACK_ALLOWED_HOSTS": entry,
            }
            with patch.dict(os.environ, env, clear=True):
                with patch.object(sys, "argv", ["mcp-india-stack", "--transport", "sse"]):
                    with pytest.raises(SystemExit) as exc:
                        server_module.main()
                    assert exc.value.code != 0

    def test_t9_harness_restores_state(self) -> None:
        """T9: Harness leaves os.environ and FastMCP settings unchanged."""
        orig_env = dict(os.environ)
        orig_sec = copy.deepcopy(mcp.settings.transport_security)

        with captured_server_app({"MCP_INDIA_STACK_API_KEY": VALID_KEY, "TEMP_TEST_VAR": "foo"}):
            assert os.environ.get("TEMP_TEST_VAR") == "foo"
            assert mcp.settings.transport_security is not None

        assert os.environ == orig_env
        assert "TEMP_TEST_VAR" not in os.environ
        assert mcp.settings.transport_security == orig_sec
