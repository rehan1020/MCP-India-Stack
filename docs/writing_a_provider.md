# Writing a Registry Provider (Level A4 Attestation)

This guide documents how to author, secure, and register custom opt-in registry providers for **Level A4 (Live Registry Attestation)** in the MCP India Stack.

---

## 1. Overview & Level A4 Semantics

The MCP India Stack defaults to **zero-auth, pure offline execution** (`A0`, `A1`, `A2`, `A3`). Live network querying of official or third-party registries is **strictly opt-in** and disabled by default.

When an end-user or agent invokes a verifying tool with `verify_online=True` (e.g., `validate_gstin(..., verify_online=True)` or `validate_pan(..., verify_online=True)`), the stack queries configured providers to verify the live registration status.

* **Status Active (`ACTIVE`)**: The entity is confirmed active by the authoritative provider. The authenticity level is promoted to `A4`, and `registry_status: "ACTIVE"` is attached to the envelope.
* **Status Inactive / Cancelled / Suspended**: The entity is valid syntactically but inactive in the registry. The level remains at `A1` (Rule R1: highest consecutive level whose checks passed), and `registry_status: "<status>"` is noted in envelope limitations.
* **Missing Fixture / Provider Error**: If the provider cannot resolve or encounters errors, the level remains at `A1` and never fabricates authenticity.

---

## 2. Base Provider Contract

All providers subclass `BaseRegistryProvider` from `mcp_india_stack.authenticity.providers`:

```python
from __future__ import annotations

from typing import Any
from mcp_india_stack.authenticity.providers import (
    BaseRegistryProvider,
    ProviderResult,
    ProviderStatus,
)


class MyCustomGstProvider(BaseRegistryProvider):
    @property
    def name(self) -> str:
        """Unique provider identifier."""
        return "my_gst_provider"

    @property
    def supported_entities(self) -> list[str]:
        """List of supported entity types (e.g. 'gstin', 'pan', 'cin')."""
        return ["gstin"]

    async def verify(self, entity_type: str, identifier: str, **kwargs: Any) -> ProviderResult:
        """Asynchronously verify identifier against upstream API."""
        # 1. Implement upstream call with timeouts and SSRF validation
        # 2. Map upstream status to ProviderStatus (ACTIVE, INACTIVE, CANCELLED, SUSPENDED, NOT_FOUND, ERROR)
        return ProviderResult(
            status=ProviderStatus.ACTIVE,
            registry_status="ACTIVE",
            source=self.name,
            as_of="2026-11-05",
            details={"legal_name": "ACME INDIA CORP"},
        )
```

The base class automatically provides `verify_sync(entity_type, identifier, **kwargs)` which manages event loop dispatch safely.

---

## 3. Mandatory Security Controls

To ensure production stability and zero disruption, all providers must respect four core security defenses:

### 3.1. SSRF Defense (Server-Side Request Forgery)
Any network provider making outbound HTTP requests must validate the destination URL using `validate_provider_url(url)`:

```python
from mcp_india_stack.authenticity.providers import validate_provider_url

validate_provider_url("https://api.upstream-gst.gov.in/v1/search")
```

The validator automatically resolves DNS and rejects:
* Loopback IPs (`127.0.0.0/8`, `::1`, `localhost`)
* Link-local addresses (`169.254.0.0/16`, `fe80::/10`)
* RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
* Multicast and reserved IP ranges

> [!NOTE]
> For isolated local test fixtures or internal mock servers, private IPs can be permitted by setting:
> `export MCP_INDIA_STACK_ALLOW_PRIVATE_PROVIDERS=1`

### 3.2. Circuit Breaker
Every registered provider is protected by a 3-state circuit breaker (`CLOSED`, `OPEN`, `HALF_OPEN`):
* **Trip Condition**: 5 consecutive upstream failures trip the breaker to `OPEN`.
* **Fast Failure**: Subsequent calls immediately fail fast without initiating network connections.
* **Cooldown**: After a 60-second cooldown period, the breaker enters `HALF_OPEN` to permit a probe request. Success resets the breaker to `CLOSED`.

### 3.3. Token-Bucket Rate Limiter
Calls through the provider registry are rate-limited via a token-bucket algorithm per provider to protect upstream quotas:
* **Default Capacity**: 10 burst requests.
* **Refill Rate**: 5 tokens per second.
* Throttled calls return `status=ProviderStatus.ERROR` with error detail `rate_limit_exceeded`.

### 3.4. Timeouts
All outbound HTTP calls must enforce strict connect and read timeouts (connect timeout $\le$ 3s, read timeout $\le$ 10s).

---

## 4. Registering a Provider

Providers can be registered via two mechanisms:

### Method A: Python Entry Points (Recommended for Packages)
Add an entry point in `pyproject.toml`:

```toml
[project.entry-points."mcp_india_stack.providers"]
my_provider = "my_package.providers:MyCustomGstProvider"
```

### Method B: Environment Variable (Configuration & Staging)
Set `MCP_INDIA_STACK_PROVIDERS` to a comma-separated list of importable classes:

```bash
export MCP_INDIA_STACK_PROVIDERS="my_package.providers.MyCustomGstProvider,my_package.providers.MyPanProvider"
```

---

## 5. Reference Implementation: `FixtureProvider`

The stack ships with a reference `FixtureProvider` for zero-network testing and offline demos. It reads pre-recorded JSON fixture responses from disk without making any external calls.

Configure the fixture directory via:
```bash
export MCP_INDIA_STACK_FIXTURE_DIR="/path/to/fixtures"
```

Fixture file layout:
```text
fixtures/
├── gstin/
│   ├── 27AAPFU0939F1ZV.json
│   └── 27AAPFU0939F1ZX.json
└── pan/
    └── ABCDE1234F.json
```

Example fixture (`27AAPFU0939F1ZV.json`):
```json
{
  "status": "ACTIVE",
  "source": "Mock GST Portal",
  "as_of": "2026-11-05",
  "details": {
    "trade_name": "ACME TRADING",
    "status": "Active"
  }
}
```
