# Contributing

## Development workflow

1. Create a feature branch
2. Make changes with tests
3. Run lint, type-check, and tests locally
4. Open a PR to `main`

## Quality requirements

All CI gates must pass locally and in pull requests:

- `ruff check .` - Linting with flake8/ruff rules
- `ruff format --check .` - Code formatting check
- `mypy src` - Strict static type checking
- `pytest tests/ -rs` - Pytest suite (must have zero skipped, zero xfailed, coverage $\ge 80\%$)
- `bandit -r src/ -ll -ii` - Bandit SAST security analysis
- `python scripts/audit_allowlist.py` - Validate pip-audit ignore configuration
- `pip-audit $(python scripts/audit_allowlist.py) -r requirements.txt` - Dependency vulnerability audit
- `python scripts/check_lock.py` - Verify requirements.txt is in sync with pyproject.toml
- `pytest tests/test_regression_guards.py -v` - Architectural invariants (Guards G01–G20)
- `python scripts/smoke_wheel.py --constants tests/constants.py` - Build and verify wheel distribution

## Managing dependencies & lockfile regeneration

We use `uv` for reproducible, universal dependency locking across platforms.

If you add or bump dependencies in `pyproject.toml`, regenerate `requirements.txt`:

```bash
uv pip compile pyproject.toml requirements.txt --extra dev --python-version 3.10 --universal -o requirements.txt
```

Verify that the lockfile is clean and free of drift:

```bash
python scripts/check_lock.py
```

Commit both `pyproject.toml` and `requirements.txt`.

## Dependabot configuration

Dependabot is configured for GitHub Actions (`github-actions`), not `pip`. Python dependencies are strictly locked via universal compile with `uv`, audited via `pip-audit` with `.pip-audit-ignore.toml`, and validated for lock drift on every PR.

## Dependency audit allowlist

Known, vetted vulnerabilities in transitive or legacy dependencies are managed in `.pip-audit-ignore.toml`.

Each entry requires:
- `id`: Advisory identifier (e.g. `GHSA-...` or `PYSEC-...`)
- `package`: Package name
- `reason`: Technical justification for the risk assessment
- `review_by`: Expiration date (`YYYY-MM-DD`). Expired entries fail CI gates.

Validated by `scripts/audit_allowlist.py` and `tests/test_audit_allowlist.py`.

## Adding new tools

When adding new tools, you must ensure compliance with regression guards:
1. **Permission Tiers (G08)**: Map every new tool in `TOOL_TIERS` in `src/mcp_india_stack/app.py` to a valid `PermissionTier`. Tools in `INITIATE` or `SUBMIT` tiers are gated behind `MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS=1`.
2. **Delegation Pattern (G11)**: Implement core business logic in a submodule under `src/mcp_india_stack/tools/`. The registration wrapper in `src/mcp_india_stack/registrations/*.py` must contain $\le 3$ statements (ignoring docstrings), no loops, no `ThreadPoolExecutor`, and no large literals.
3. **Core Schema Coverage (G19)**: If the new tool is designated as a core schema tool, add its name to `SCHEMA_TOOLS` in `tests/constants.py`.
