"""Provider discovery, management, and resilient execution coordination."""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
import os
from typing import Any

from mcp_india_stack.authenticity.providers.base import BaseRegistryProvider
from mcp_india_stack.authenticity.providers.fixture_provider import FixtureProvider
from mcp_india_stack.authenticity.providers.models import ProviderResult, ProviderStatus
from mcp_india_stack.authenticity.providers.security import (
    CircuitBreaker,
    TokenBucketRateLimiter,
)

_logger = logging.getLogger(__name__)

# Registered providers cache
_REGISTERED_PROVIDERS: list[BaseRegistryProvider] = []
_CIRCUIT_BREAKERS: dict[str, CircuitBreaker] = {}
_RATE_LIMITERS: dict[str, TokenBucketRateLimiter] = {}
_INITIALIZED: bool = False


def register_provider(provider: BaseRegistryProvider) -> None:
    """Explicitly register a provider instance."""
    _REGISTERED_PROVIDERS.append(provider)
    if provider.name not in _CIRCUIT_BREAKERS:
        _CIRCUIT_BREAKERS[provider.name] = CircuitBreaker()
    if provider.name not in _RATE_LIMITERS:
        _RATE_LIMITERS[provider.name] = TokenBucketRateLimiter()


def clear_providers() -> None:
    """Clear all registered providers and security state (used in testing)."""
    global _INITIALIZED
    _REGISTERED_PROVIDERS.clear()
    _CIRCUIT_BREAKERS.clear()
    _RATE_LIMITERS.clear()
    _INITIALIZED = False


def _discover_providers() -> None:
    """Discover providers from entry points and environment variables."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    # 1. Entry point discovery
    try:
        eps = importlib.metadata.entry_points(group="mcp_india_stack.providers")
        for ep in eps:
            try:
                cls_ = ep.load()
                provider = cls_()
                if isinstance(provider, BaseRegistryProvider):
                    register_provider(provider)
            except Exception as exc:
                _logger.warning("Failed loading provider entry point '%s': %s", ep.name, exc)
    except Exception:
        pass

    # 2. Environment variable discovery (comma-separated class paths)
    env_providers = os.environ.get("MCP_INDIA_STACK_PROVIDERS", "").strip()
    if env_providers:
        for item in env_providers.split(","):
            path = item.strip()
            if not path:
                continue
            try:
                if "." in path:
                    mod_name, cls_name = path.rsplit(".", 1)
                    mod = importlib.import_module(mod_name)
                    cls_ = getattr(mod, cls_name)
                    provider = cls_()
                    if isinstance(provider, BaseRegistryProvider):
                        register_provider(provider)
            except Exception as exc:
                _logger.warning("Failed loading provider from environment '%s': %s", path, exc)

    # 3. Default fallback: If MCP_INDIA_STACK_FIXTURE_DIR is set, enable FixtureProvider
    if os.environ.get("MCP_INDIA_STACK_FIXTURE_DIR") and not _REGISTERED_PROVIDERS:
        register_provider(FixtureProvider())


def get_provider_for_entity(entity_type: str) -> BaseRegistryProvider | None:
    """Find the first matching provider that supports the given entity type."""
    _discover_providers()
    clean_entity = entity_type.strip().lower()
    for provider in _REGISTERED_PROVIDERS:
        if clean_entity in [e.lower() for e in provider.supported_entities]:
            return provider
    return None


def execute_provider_verification(
    entity_type: str, identifier: str, **kwargs: Any
) -> ProviderResult | None:
    """Execute provider verification with circuit breaker, rate limiter, and timeouts."""
    provider = get_provider_for_entity(entity_type)
    if provider is None:
        return None

    p_name = provider.name
    cb = _CIRCUIT_BREAKERS.setdefault(p_name, CircuitBreaker())
    limiter = _RATE_LIMITERS.setdefault(p_name, TokenBucketRateLimiter())

    if not cb.can_execute():
        return ProviderResult(
            status=ProviderStatus.ERROR,
            details={"error": "circuit_breaker_open"},
            source=p_name,
            error_message="Provider circuit breaker is OPEN due to repeated upstream failures",
        )

    if not limiter.acquire():
        return ProviderResult(
            status=ProviderStatus.ERROR,
            details={"error": "rate_limit_exceeded"},
            source=p_name,
            error_message="Provider rate limit exceeded. Request throttled.",
        )

    try:
        result = provider.verify_sync(entity_type, identifier, **kwargs)
        if result.status in (
            ProviderStatus.ACTIVE,
            ProviderStatus.INACTIVE,
            ProviderStatus.CANCELLED,
            ProviderStatus.SUSPENDED,
            ProviderStatus.NOT_FOUND,
        ):
            cb.record_success()
        else:
            cb.record_failure()
        if result.rate_limit_remaining is None:
            result = ProviderResult(
                status=result.status,
                registry_status=result.registry_status,
                details=result.details,
                raw_evidence=result.raw_evidence,
                source=result.source,
                as_of=result.as_of,
                error_message=result.error_message,
                rate_limit_remaining=limiter.remaining,
            )
        return result
    except Exception as exc:
        cb.record_failure()
        return ProviderResult(
            status=ProviderStatus.ERROR,
            details={"exception": str(exc)},
            source=p_name,
            error_message=f"Provider exception: {exc}",
            rate_limit_remaining=limiter.remaining,
        )
