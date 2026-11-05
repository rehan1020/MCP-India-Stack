"""Tests for Authenticity System 8d: Opt-in Registry Provider Interface (Level A4).

Verifies:
1. BaseRegistryProvider interface and async/sync contract conformance.
2. FixtureProvider end-to-end promotion to Level A4 on active registry attestation.
3. Negative attestation (cancelled/inactive): Level stays at A1/A0 per Rule R1.
4. Missing fixture / unmapped entity handles gracefully without errors.
5. Circuit breaker trips to OPEN on repeated failures, fast-fails during cooldown, recovers.
6. SSRF defense blocks loopback, RFC 1918 private, link-local, and reserved destinations.
7. SSRF defense bypass when MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS=1.
8. Token-bucket rate limiter throttles burst requests exceeding capacity.
9. Strict offline guarantee: verify_online=False never touches network or providers.
10. Dynamic provider discovery via MCP_INDIA_STACK_PROVIDERS environment variable.
"""

from __future__ import annotations

import asyncio
import os
import socket
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from mcp_india_stack.authenticity.providers import (
    BaseRegistryProvider,
    CircuitBreaker,
    FixtureProvider,
    ProviderResult,
    ProviderStatus,
    SSRFError,
    TokenBucketRateLimiter,
    clear_providers,
    execute_provider_verification,
    register_provider,
    validate_provider_url,
)
from mcp_india_stack.tools.cin import validate_cin
from mcp_india_stack.tools.gstin import validate_gstin
from mcp_india_stack.tools.pan import validate_pan

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "providers"


@pytest.fixture(autouse=True)
def _reset_provider_state():
    """Ensure clean provider registry state before and after each test."""
    clear_providers()
    yield
    clear_providers()


class MockCustomProvider(BaseRegistryProvider):
    """Test provider implementing contract."""

    def __init__(self, name: str = "mock_provider", status: ProviderStatus = ProviderStatus.ACTIVE):
        self._name = name
        self._status = status
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_entities(self) -> list[str]:
        return ["gstin", "pan"]

    async def verify(self, entity_type: str, identifier: str, **kwargs: Any) -> ProviderResult:
        self.call_count += 1
        await asyncio.sleep(0.001)
        return ProviderResult(
            status=self._status,
            registry_status=self._status.value,
            details={"verified": True, "id": identifier},
            source=self.name,
            as_of="2026-11-05",
        )


def test_provider_contract_conformance() -> None:
    """BaseRegistryProvider executes both async and sync verify methods properly."""
    provider = MockCustomProvider(name="test_contract")
    assert provider.name == "test_contract"
    assert "gstin" in provider.supported_entities

    # Sync invocation
    res_sync = provider.verify_sync("gstin", "27AAPFU0939F1ZV")
    assert isinstance(res_sync, ProviderResult)
    assert res_sync.status == ProviderStatus.ACTIVE
    assert res_sync.registry_status == "ACTIVE"
    assert res_sync.source == "test_contract"

    # Async invocation
    res_async = asyncio.run(provider.verify("gstin", "27AAPFU0939F1ZV"))
    assert res_async.status == ProviderStatus.ACTIVE


def test_fixture_provider_active_match_promotes_to_a4(monkeypatch: pytest.MonkeyPatch) -> None:
    """FixtureProvider active match promotes authenticity level to A4 with registry_status."""
    fixture_provider = FixtureProvider(fixture_dir=FIXTURES_DIR)
    register_provider(fixture_provider)

    # validate_gstin with verify_online=True
    res = validate_gstin("27AAPFU0939F1ZV", verify_online=True)
    assert res["success"] is True
    assert res["data"]["valid"] is True
    assert res["data"]["registry_status"] == "ACTIVE"

    auth = res["authenticity"]
    assert auth["level"] == "A4"
    assert auth["registry_status"] == "ACTIVE"
    assert any(c["name"] == "registry_provider_attestation" and c["passed"] for c in auth["checks"])
    assert not any("active registration status not verified" in lim for lim in auth["limitations"])


def test_fixture_provider_cancelled_match_retains_a1() -> None:
    """FixtureProvider cancelled match keeps level at A1 per Rule R1 (no level inflation)."""
    fixture_provider = FixtureProvider(fixture_dir=FIXTURES_DIR)
    register_provider(fixture_provider)

    # 29AAPFU0939F1ZR is cancelled in fixture
    res = validate_gstin("29AAPFU0939F1ZR", verify_online=True)
    assert res["success"] is True
    assert res["data"]["valid"] is True
    assert res["data"]["registry_status"] == "CANCELLED"

    auth = res["authenticity"]
    # Level must stay at A1 because A4 check did NOT pass (Rule R1)
    assert auth["level"] == "A1"
    # registry_status is absent unless level == A4
    assert "registry_status" not in auth
    assert any(
        c["name"] == "registry_provider_attestation" and not c["passed"] for c in auth["checks"]
    )
    assert any("registry_status:cancelled" in lim for lim in auth["limitations"])


def test_fixture_provider_pan_active_match() -> None:
    """PAN validation with verify_online=True promotes to A4 on operative record."""
    fixture_provider = FixtureProvider(fixture_dir=FIXTURES_DIR)
    register_provider(fixture_provider)

    res = validate_pan("ABCPE1234F", verify_online=True)
    assert res["valid"] is True
    assert res["data"]["registry_status"] == "ACTIVE"

    auth = res["authenticity"]
    assert auth["level"] == "A4"
    assert auth["registry_status"] == "ACTIVE"


def test_fixture_provider_missing_fixture_retains_a1() -> None:
    """Missing fixture returns NOT_FOUND status, keeping level at A1 without crashing."""
    fixture_provider = FixtureProvider(fixture_dir=FIXTURES_DIR)
    register_provider(fixture_provider)

    # Unknown PAN with valid format/entity (ABCPZ9999Z) but no JSON fixture on disk
    res = validate_pan("ABCPZ9999Z", verify_online=True)
    assert res["valid"] is True
    auth = res["authenticity"]
    assert auth["level"] == "A1"
    assert any("registry_status:not_found" in lim for lim in auth["limitations"])


def test_circuit_breaker_tripping_and_recovery() -> None:
    """Circuit breaker trips to OPEN after 5 failures and recovers after cooldown."""
    cb = CircuitBreaker(failure_threshold=5, cooldown_seconds=0.1)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    # Record 4 failures: remains CLOSED
    for _ in range(4):
        cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    # 5th failure: trips to OPEN
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Wait for cooldown
    time.sleep(0.12)
    # Probe permitted (HALF_OPEN)
    assert cb.can_execute() is True
    assert cb.state == "HALF_OPEN"

    # Successful probe restores to CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True


def test_circuit_breaker_in_registry_execution() -> None:
    """Circuit breaker prevents repetitive upstream execution on open state."""
    failing_provider = MockCustomProvider(name="failing_mock", status=ProviderStatus.ERROR)
    register_provider(failing_provider)

    # Trigger 5 errors to trip breaker
    for _ in range(5):
        execute_provider_verification("gstin", "27AAPFU0939F1ZV")

    # 6th attempt should fast-fail with circuit_breaker_open
    res = execute_provider_verification("gstin", "27AAPFU0939F1ZV")
    assert res is not None
    assert res.status == ProviderStatus.ERROR
    assert res.details.get("error") == "circuit_breaker_open"


def test_ssrf_blocks_forbidden_destinations() -> None:
    """validate_provider_url blocks loopback, private, link-local, and reserved destinations."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS", None)

        # Loopback
        with pytest.raises(SSRFError, match="(?i)loopback|SSRF"):
            validate_provider_url("http://127.0.0.1:8080/check")

        with pytest.raises(SSRFError, match="(?i)loopback|SSRF"):
            validate_provider_url("http://localhost:5000/api")

        # Link-local / AWS metadata
        with pytest.raises(SSRFError, match="(?i)link-local|SSRF"):
            validate_provider_url("http://169.254.169.254/latest/meta-data")

        # RFC 1918 private subnets
        with pytest.raises(SSRFError, match="(?i)private|SSRF"):
            validate_provider_url("http://10.0.0.1/verify")

        with pytest.raises(SSRFError, match="(?i)private|SSRF"):
            validate_provider_url("http://192.168.1.1:8000/gst")

        with pytest.raises(SSRFError, match="(?i)private|SSRF"):
            validate_provider_url("http://172.16.0.1/status")


def test_ssrf_bypass_with_env_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """SSRF validation permits private IP targets when explicit env flag is enabled."""
    monkeypatch.setenv("MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS", "1")
    # Should not raise
    validate_provider_url("http://127.0.0.1:8080/check")
    validate_provider_url("http://192.168.1.1/api")


def test_token_bucket_rate_limiter() -> None:
    """Token bucket rate limiter enforces capacity caps and throttles excess calls."""
    limiter = TokenBucketRateLimiter(rate=1.0, capacity=2.0)
    assert limiter.remaining == 2
    assert limiter.acquire(1.0) is True
    assert limiter.acquire(1.0) is True
    # Capacity exhausted
    assert limiter.acquire(1.0) is False


def test_offline_guarantee_zero_sockets_when_verify_online_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verify_online=False guarantees zero network socket connections and zero provider calls."""
    provider_mock = MockCustomProvider(name="spy_provider")
    register_provider(provider_mock)

    # Block socket connections
    def _fail_socket(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Unexpected network socket access in offline-first mode")

    monkeypatch.setattr(socket, "socket", _fail_socket)
    monkeypatch.setattr(socket, "create_connection", _fail_socket)

    # Verify calls with verify_online=False
    res_gst = validate_gstin("27AAPFU0939F1ZV", verify_online=False)
    assert res_gst["data"]["valid"] is True
    assert res_gst["authenticity"]["level"] == "A1"

    res_pan = validate_pan("ABCPE1234F", verify_online=False)
    assert res_pan["valid"] is True
    assert res_pan["authenticity"]["level"] == "A1"

    res_cin = validate_cin("L17110MH1973PLC019786", verify_online=False)
    assert res_cin["data"]["valid"] is True
    assert res_cin["authenticity"]["level"] == "A1"

    # Provider should never have been invoked
    assert provider_mock.call_count == 0


def test_provider_discovery_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Providers are dynamically discovered and instantiated from MCP_INDIA_STACK_PROVIDERS."""
    monkeypatch.setenv(
        "MCP_INDIA_STACK_PROVIDERS",
        "mcp_india_stack.authenticity.providers.FixtureProvider",
    )
    clear_providers()

    res = execute_provider_verification("gstin", "27AAPFU0939F1ZV")
    assert res is not None
    assert res.source == "FixtureProvider" or "Mock" in res.source
