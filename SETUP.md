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

## 4. Refresh datasets

```bash
python scripts/update_datasets.py --refresh-all
```

Alternatively, refresh individual datasets:
```bash
python scripts/update_datasets.py --refresh-ifsc --refresh-pincode --refresh-hsn
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
python -m zipfile -l dist/mcp_india_stack-0.6.3-py3-none-any.whl
```

## 7. PyPI publish setup

Preferred: Trusted Publishing (OIDC)

1. In PyPI project settings, add trusted publisher for this repo/workflow:
	 - Repository: `rehan1020/MCP-India-Stack`
	 - Workflow: `.github/workflows/publish.yml`
	 - Environment: optional
2. Push tag:

```bash
git tag v0.6.3
git push origin v0.6.3
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

When running with `--transport sse` (e.g. on Render), the server supports several security controls via environment variables:

### `MCP_INDIA_STACK_API_KEY`

If set, every HTTP request to the SSE server must include a `Authorization: Bearer <key>` header matching this value. Requests without a valid token receive a `401 Unauthorized` response.

If unset, the server starts in unauthenticated mode and logs a warning at startup.

### `MCP_INDIA_STACK_ALLOWED_ORIGINS`

Comma-separated list of allowed CORS origins (e.g. `https://example.com,https://app.example.com`).

- **Unset/empty**: Cross-origin requests are rejected (no origins allowed, credentials disabled).
- **Set**: Only listed origins are allowed, credentials are enabled.
- **Never set to `*`**: The server will refuse to start if `*` is combined with credentials.

### `MCP_INDIA_STACK_RATE_LIMIT`

Rate limit in `<requests>/<window_seconds>` format (e.g. `60/60` = 60 requests per minute).

Default: `60/60`. Applied per IP address, or per API key if `MCP_INDIA_STACK_API_KEY` is set.

### `MCP_INDIA_STACK_BULK_WORKERS`

Maximum number of concurrent workers for bulk validation tools (`bulk_validate_gstin`, `bulk_validate_ifsc`, `bulk_validate_pan`, `bulk_validate_aadhaar`).

- Valid range: **1–20** (values outside this range are clamped)
- Default: `10`
- Non-integer input falls back to default
