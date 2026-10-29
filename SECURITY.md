# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please send an email to the maintainers. We appreciate responsible disclosure and will work to address issues promptly.

## Supported Versions

We release patches for security vulnerabilities. Which versions are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| < 0.6   | :x:                |

## Active Security Controls

The `mcp-india-stack` server implements defence-in-depth architectural security controls verified continuously in CI by regression guards (`tests/test_regression_guards.py`):

1. **API Key Minimum Length (Guard G15, Issue I2)**: Server refuses startup if `MCP_INDIA_STACK_API_KEY` is configured and is shorter than 32 characters.
2. **Constant-Time Token Comparison (Guard G02, Issue I2)**: Bearer tokens are validated using `hmac.compare_digest` to prevent timing side-channel attacks.
3. **Failed-Authentication Throttling (Guard G17, Issue I2)**: Bounded in-memory sliding window tracks failed authentication attempts per client IP (`MCP_INDIA_STACK_AUTH_FAIL_LIMIT`, default 10). Excess failed attempts are rejected with HTTP 429 Too Many Requests and a `Retry-After` header. Valid authentication passes directly and never touches the failure store.
4. **Key-Hashed Rate Limiting (Guard G18, Issue I2)**: Request rate limiting operates over a bounded store using the truncated SHA-256 digest prefix of the API key (`key:<sha256[:16]>`) rather than raw bearer tokens. Unauthenticated requests are keyed by client IP (`ip:<client_host>`).
5. **CORS Allowlist & Protection (Guard G01, G14, Issue I1)**: CORS origin allowlist is strictly configured via `MCP_INDIA_STACK_ALLOWED_ORIGINS`. Combining wildcard origins (`*`) with credentials is explicitly forbidden at startup. Preflight `OPTIONS` requests are handled by outermost CORS middleware without requiring authentication credentials.
6. **Host & Origin Allowlist (Guard G16, Issue I1)**: FastMCP transport security enforces DNS rebinding protection and host allowlists using loopback interfaces, `MCP_INDIA_STACK_ALLOWED_HOSTS`, and cloud deployment hostnames (e.g. `RENDER_EXTERNAL_HOSTNAME`).
7. **Fail-Closed Startup Safeguards (Guard G13, G15, Issue I2)**: Binding to non-loopback addresses (`0.0.0.0` or public interfaces) without an API key fails startup immediately unless explicitly opted-in via `MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK=1`.
8. **Bundled & Checksum-Verified Datasets (Guard G04, G05, Issue I3)**: All dataset assets are bundled offline with release packages and verified against cryptographic SHA-256 checksums in `dataset_checksums.json`. Runtime network fetches and dynamic updates are entirely disabled.
9. **Elevated-Tool Gate (Guard G08, Issue I6)**: Tools classified in `INITIATE` and `SUBMIT` permission tiers (such as drafting legal applications or consent requests) are disabled and omitted from the tool list unless explicitly enabled via `MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS=1`.
10. **Pseudonymized Telemetry (Guard G07, Issue I5)**: Telemetry is strictly opt-in and disabled unless `MCP_INDIA_STACK_TELEMETRY_PEPPER` is configured. When enabled, tool identifiers and inputs are hashed via HMAC-SHA256 using the secret pepper, guaranteeing that raw PII (such as PAN or Aadhaar numbers) is never written to disk or logs.
