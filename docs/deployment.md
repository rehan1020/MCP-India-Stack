# Remote SSE Transport & Deployment Guide

This document describes the remote Server-Sent Events (SSE) transport for `mcp-india-stack`, its security architecture, configuration options, and deployment instructions on cloud providers such as Render.

---

## 1. Architecture Overview

`mcp-india-stack` supports both local `stdio` (default) and remote `sse` transports:
- **`stdio` transport**: Default for local agent clients (Claude Desktop, Antigravity CLI, cursor).
- **`sse` transport**: Designed for containerized deployments, remote agents, and cloud platforms (e.g. Render, Railway, Fly.io, Kubernetes).

```text
                  +----------------------------------------------+
                  |               Client / AI Agent              |
                  +----------------------------------------------+
                                |               |
           GET /sse (Stream)    |               | POST /messages/ (JSON-RPC)
        (Bearer Token / CORS)   |               |   (Bearer Token / CORS)
                                v               v
                  +----------------------------------------------+
                  |            mcp-india-stack SSE               |
                  |                                              |
                  |  [CORS Middleware]                           |
                  |  [Body Limit Middleware (1MB)]               |
                  |  [Bearer Auth Middleware (HMAC)]             |
                  |  [Rate Limiting Middleware (Token Bucket)]   |
                  |  [DNS Rebinding Protection]                  |
                  |                                              |
                  |  Endpoints:                                  |
                  |    - /health, /healthz, / (Unauthenticated)  |
                  |    - /sse (Event Stream)                     |
                  |    - /messages/ (Tool execution)             |
                  +----------------------------------------------+
```

---

## 2. Endpoints & Authentication

### Unauthenticated Health Endpoints
- **`GET /health`** or **`GET /healthz`**: Returns `{"status": "ok", "version": "<version>"}`. Used by load balancers and orchestrators for liveness/readiness probes.
- **`GET /`**: Returns basic service metadata: `{"status": "ok", "service": "mcp-india-stack", "version": "<version>"}`.

### Authenticated Endpoints
- **`GET /sse`**: Initiates the persistent Server-Sent Events stream. Returns endpoint URI for message submission.
- **`POST /messages/`**: Submits JSON-RPC 2.0 tool invocation calls.

### Authentication Mechanism
Authentication uses HTTP Bearer tokens via the standard header:
```http
Authorization: Bearer <MCP_INDIA_STACK_API_KEY>
```
- **Constant-time comparison**: Token verification uses `hmac.compare_digest` over SHA-256 digests to protect against timing attacks.
- **Brute force throttling**: Excessive failed authentication attempts are throttled with HTTP 429 and a `Retry-After` header.
- **Fail-closed startup**: The server strictly refuses to bind to non-loopback interfaces (e.g., `0.0.0.0`) without an API key unless explicitly overridden.

---

## 3. Environment Variables Reference

| Variable | Description | Default | Example |
|---|---|---|---|
| `PORT` | HTTP port to listen on. | `8000` | `10000` |
| `MCP_INDIA_STACK_API_KEY` | Bearer token required for all SSE requests (min 32 characters). | _None_ (Required for non-loopback) | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `MCP_INDIA_STACK_RATE_LIMIT` | Max requests per time window in `<requests>/<seconds>`. | `60/60` | `120/60` |
| `MCP_INDIA_STACK_AUTH_FAIL_LIMIT`| Failed auth attempts allowed per minute before IP throttle. | `10` | `5` |
| `MCP_INDIA_STACK_MAX_BODY_SIZE` | Maximum allowed request payload body in bytes. | `1048576` (1MB) | `2097152` |
| `MCP_INDIA_STACK_ALLOWED_ORIGINS`| Comma-separated list of allowed CORS origins. | `""` | `https://myagent.com,https://app.example.com` |
| `MCP_INDIA_STACK_ALLOWED_HOSTS` | Comma-separated list of allowed `Host` headers. | Loopback hosts | `api.example.com,mcp-india-stack.onrender.com` |
| `MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK` | Set to `1` to override auth check on `0.0.0.0` (testing only). | `""` | `0` |

---

## 4. Local Execution

Run the SSE server locally on the loopback interface:

```bash
# Minimal local execution on 127.0.0.1:8000
mcp-india-stack --transport sse

# With authentication and custom port
export MCP_INDIA_STACK_API_KEY="my_secret_token_at_least_32_characters_long"
mcp-india-stack --transport sse --port 8080
```

Verify the service is running:
```bash
curl http://127.0.0.1:8080/health
# {"status":"ok","version":"0.8.0"}
```

---

## 5. Deployment on Render

The repository contains a production-ready [`render.yaml`](../render.yaml) specification:

```yaml
services:
  - type: web
    name: mcp-india-stack
    env: python
    buildCommand: pip install .
    startCommand: mcp-india-stack --transport sse --host 0.0.0.0
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: "10000"
      - key: PYTHONUNBUFFERED
        value: "1"
      - key: MCP_INDIA_STACK_API_KEY
        fromSecret: MCP_INDIA_STACK_API_KEY
      - key: MCP_INDIA_STACK_ALLOWED_ORIGINS
        value: ""
      - key: MCP_INDIA_STACK_RATE_LIMIT
        value: "60/60"
    plan: free
```

### Steps to Deploy:
1. Connect your GitHub repository to [Render](https://render.com).
2. Choose **New Blueprints Instance** and select this repository.
3. Set the secret environment variable `MCP_INDIA_STACK_API_KEY` in the Render Dashboard (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
4. Render will build the package, deploy the service, verify `/health`, and assign a public HTTPS URL (e.g. `https://mcp-india-stack.onrender.com`).
