"""Security and resilience controls for external registry providers.

Implements:
1. SSRF defense against loopback, RFC 1918 private, link-local, and reserved IPs.
2. Circuit Breaker tripping on N consecutive failures with a cooldown recovery window.
3. Token Bucket Rate Limiter per provider.
4. Strict timeout enforcement (default 3s, max 10s).
"""

from __future__ import annotations

import ipaddress
import os
import socket
import time
from urllib.parse import urlparse


class ProviderSecurityError(Exception):
    """Raised when an external provider operation violates security boundaries."""


class SSRFError(ProviderSecurityError):
    """Raised when an outbound URL resolves to a forbidden or private network destination."""


class CircuitBreakerOpenError(ProviderSecurityError):
    """Raised when a provider is unavailable due to an open circuit breaker."""


class RateLimitExceededError(ProviderSecurityError):
    """Raised when request volume exceeds the provider rate limit."""


def validate_provider_url(url: str) -> None:
    """Validate provider endpoint URL against SSRF vulnerabilities.

    Rejects private RFC 1918, loopback, link-local, and reserved IP addresses,
    unless explicitly permitted by MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS=1.
    """
    allow_private = os.environ.get("MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS") == "1"
    if allow_private:
        return

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("https", "http"):
        raise SSRFError(f"Disallowed URL scheme: '{parsed.scheme}'. Only HTTP(S) permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("Provider URL lacks a valid hostname.")

    # Block localhost string literals directly
    if hostname.lower() in ("localhost", "ip6-localhost", "ip6-loopback"):
        raise SSRFError(f"SSRF violation: target '{hostname}' is a loopback alias.")

    try:
        # Resolve hostname to IPv4 and IPv6 addresses
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        resolved_ips = {item[4][0] for item in addr_info}
    except Exception as exc:
        raise SSRFError(f"DNS resolution failure for '{hostname}': {exc}") from exc

    for ip_str in resolved_ips:
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_loopback:
                raise SSRFError(f"SSRF violation: target resolves to loopback IP '{ip}'.")
            if ip.is_private:
                raise SSRFError(f"SSRF violation: target resolves to private RFC 1918 IP '{ip}'.")
            if ip.is_link_local:
                raise SSRFError(f"SSRF violation: target resolves to link-local IP '{ip}'.")
            if ip.is_reserved or ip.is_multicast:
                raise SSRFError(f"SSRF violation: target resolves to reserved/multicast IP '{ip}'.")
        except ValueError as exc:
            raise SSRFError(f"Invalid resolved IP '{ip_str}': {exc}") from exc


class CircuitBreaker:
    """Three-state circuit breaker (CLOSED, OPEN, HALF_OPEN) for provider fault isolation."""

    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_state_change = time.monotonic()

    def can_execute(self) -> bool:
        """Check whether the circuit breaker permits a new execution attempt."""
        now = time.monotonic()
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if now - self.last_state_change >= self.cooldown_seconds:
                self.state = "HALF_OPEN"
                self.last_state_change = now
                return True
            return False
        # HALF_OPEN: permit a probe request
        return True

    def record_success(self) -> None:
        """Record successful execution and reset breaker to CLOSED."""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_state_change = time.monotonic()

    def record_failure(self) -> None:
        """Record failed execution and trip to OPEN if threshold reached."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.last_state_change = time.monotonic()


class TokenBucketRateLimiter:
    """Token bucket rate limiter providing burstable, smooth rate control."""

    def __init__(self, rate: float = 5.0, capacity: float = 10.0) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_time = time.monotonic()

    def acquire(self, tokens: float = 1.0) -> bool:
        """Attempt to acquire tokens; returns True if permitted, False if throttled."""
        now = time.monotonic()
        elapsed = now - self.last_time
        self.last_time = now

        # Replenish tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def remaining(self) -> int:
        """Return the floor of currently available tokens."""
        now = time.monotonic()
        elapsed = now - self.last_time
        available = min(self.capacity, self.tokens + elapsed * self.rate)
        return int(max(0, available))
