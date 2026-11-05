"""Pluggable registry provider interface for Level A4 attestation."""

from __future__ import annotations

from mcp_india_stack.authenticity.providers.base import BaseRegistryProvider
from mcp_india_stack.authenticity.providers.fixture_provider import FixtureProvider
from mcp_india_stack.authenticity.providers.models import ProviderResult, ProviderStatus
from mcp_india_stack.authenticity.providers.registry import (
    clear_providers,
    execute_provider_verification,
    get_provider_for_entity,
    register_provider,
)
from mcp_india_stack.authenticity.providers.security import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    ProviderSecurityError,
    RateLimitExceededError,
    SSRFError,
    TokenBucketRateLimiter,
    validate_provider_url,
)

__all__ = [
    "BaseRegistryProvider",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "FixtureProvider",
    "ProviderResult",
    "ProviderSecurityError",
    "ProviderStatus",
    "RateLimitExceededError",
    "SSRFError",
    "TokenBucketRateLimiter",
    "clear_providers",
    "execute_provider_verification",
    "get_provider_for_entity",
    "register_provider",
    "validate_provider_url",
]
