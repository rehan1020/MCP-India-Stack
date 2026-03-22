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
python -m zipfile -l dist/mcp_india_stack-0.1.0-py3-none-any.whl
```

## 7. PyPI publish setup

Preferred: Trusted Publishing (OIDC)

1. In PyPI project settings, add trusted publisher for this repo/workflow:
	 - Repository: `rehan1020/MCP-India-Stack`
	 - Workflow: `.github/workflows/publish.yml`
	 - Environment: optional
2. Push tag:

```bash
git tag v0.1.0
git push origin v0.1.0
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

