# SETUP.md

## 1. Create GitHub org and repository

1. Create org: `mcp-india-stack`
2. Create repo: `mcp-india-stack` (public)
3. Set description:
	 - `MCP server exposing Indian financial and government APIs - GSTIN, IFSC, PAN, UPI, pincode, HSN/SAC - for AI agents. Zero auth. Offline-first.`

## 2. Branch protection (main)

Enable the following on `main`:

- Require a pull request before merging
- Require approvals: 1
- Dismiss stale approvals on new commits
- Require status checks to pass before merging: `CI / test (3.10)`, `CI / test (3.11)`, `CI / test (3.12)`
- Require conversation resolution before merging
- Restrict force pushes
- Restrict deletions

## 3. Local bootstrap

```bash
python -m venv .venv
. .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
pre-commit install
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## 4. Upstream datasets (maintainers)

Datasets are bundled offline in the package. Maintainers can refresh upstream datasets and regenerate checksums:
```bash
python scripts/update_datasets.py --refresh-ifsc --refresh-pincode --refresh-hsn
```
Or regenerate checksum manifests without downloading:
```bash
python scripts/update_datasets.py --write-checksums
```

If HSN auto-download fails, manually download `HSN_SAC.xlsx` and place at `staging/HSN_SAC.xlsx`, then rerun.

## 5. Run checks

```bash
ruff check .
ruff format --check .
mypy src
pytest --cov=mcp_india_stack --cov-report=term-missing --cov-fail-under=80
```

## 6. Build package

```bash
python -m build
```

Verify wheel contents include data files:

```bash
python -m zipfile -l dist/mcp_india_stack-0.6.7-py3-none-any.whl
```

## 7. PyPI publish setup

Preferred: Trusted Publishing (OIDC)

1. In PyPI project settings, add trusted publisher for this repo/workflow:
	 - Repository: `rehan1020/MCP-India-Stack`
	 - Workflow: `.github/workflows/publish.yml`
	 - Environment: optional
2. Push tag:

```bash
git tag v0.6.7
git push origin v0.6.7
```

Fallback: use `PYPI_API_TOKEN` GitHub secret and twine workflow (not included here).

## 8. Claude Desktop MCP config

Windows config path:
`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
	"mcpServers": {
		"mcp-india-stack": {
			"command": "C:\\Python312\\python.exe",
			"args": ["-m", "mcp_india_stack"]
		}
	}
}
```

macOS config path:
`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
	"mcpServers": {
		"mcp-india-stack": {
			"command": "/usr/bin/python3",
			"args": ["-m", "mcp_india_stack"]
		}
	}
}
```

Linux config path:
`~/.config/Claude/claude_desktop_config.json`

```json
{
	"mcpServers": {
		"mcp-india-stack": {
			"command": "/usr/bin/python3",
			"args": ["-m", "mcp_india_stack"]
		}
	}
}
```

## 9. SSE Transport Security

When running with `--transport sse` (e.g. on Render), the server binds to loopback (`127.0.0.1`) by default for safety. For cloud or containerized environments (such as Render), specify `--host 0.0.0.0` explicitly.

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MCP_INDIA_STACK_API_KEY` | Secret bearer token required for requests (minimum 32 characters). Generated via `python -c "import secrets; print(secrets.token_urlsafe(32))"`. | None (unauthenticated) |
| `MCP_INDIA_STACK_AUTH_FAIL_LIMIT` | Maximum failed authentication attempts allowed per client IP within a 60-second window before throttling with HTTP 429 and `Retry-After`. | `10` |
| `MCP_INDIA_STACK_ALLOWED_HOSTS` | Comma-separated list of additional allowed host headers for DNS rebinding protection (e.g. `api.example.com`). Bare hostnames automatically allow both port-wildcard (`H:*`) and portless (`H`) hosts. | Loopback hosts only (`127.0.0.1`, `localhost`, `[::1]`) |
| `MCP_INDIA_STACK_ALLOWED_ORIGINS` | Comma-separated list of allowed origins. Feeds both Starlette `CORSMiddleware` and MCP SDK transport security origin checks (e.g. `https://app.example.com`). Wildcards with credentials are strictly forbidden. | Empty (cross-origin disabled) |
| `MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK` | Set to `"1"` to explicitly permit binding to a non-loopback address without configuring an API key. Otherwise, non-loopback startup without a key is refused. | Unset |
| `MCP_INDIA_STACK_RATE_LIMIT` | Sliding window rate limit in `<requests>/<window_seconds>` format (e.g. `60/60`). Keyed by token hash when authenticated, or client IP when unauthenticated. | `60/60` |
| `MCP_INDIA_STACK_BULK_WORKERS` | Maximum concurrent threads for bulk validation tools (`bulk_validate_gstin`, `bulk_validate_ifsc`, `bulk_validate_pan`, `bulk_validate_aadhaar`), clamped to 1–20. | `10` |

### Client Authentication

Clients must send the configured API key in the standard HTTP `Authorization` header:

```http
Authorization: Bearer <your-32-plus-character-api-key>
```

- Valid requests pass directly without touching the authentication failure throttle.
- Missing or invalid tokens count as failures against the caller host. Exceeding `MCP_INDIA_STACK_AUTH_FAIL_LIMIT` returns HTTP 429 Too Many Requests with a `Retry-After` header.
- Valid requests are rate-limited separately by a truncated SHA-256 hash of the validated token (`key:<hash[:16]>`), preventing raw tokens from ever being stored in memory.

### Render & Reverse Proxy Deployment

- **Automatic Host Detection**: Render sets `RENDER_EXTERNAL_HOSTNAME` (e.g. `mcp-india-stack.onrender.com`), which the server automatically includes in `allowed_hosts`.
- **Custom Domains**: If using a custom domain (e.g. `mcp.mycompany.com`), configure `MCP_INDIA_STACK_ALLOWED_HOSTS=mcp.mycompany.com`.
- **Client IP Attribution**: Behind Render's reverse proxy, connecting socket peers are Render's internal proxy routers. As a result, `request.client.host` attributes to the proxy IP. This means the authentication failure throttle acts as a global brute-force ceiling across failed attempts. Valid tokens are completely immune to failure throttling and will never be locked out by third-party failures. With a single shared API key, validated-token rate limiting functions effectively across all clients sharing that key.
