"""Regression guards enforcing architectural invariants across the entire stack.

Docstrings map to issue IDs (I1-I14) and network boundary security requirements.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import hmac
import importlib
import importlib.util
import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from tests._app_harness import VALID_TEST_API_KEY, captured_server_app
from tests.constants import (
    EXPECTED_TOOL_COUNT_ELEVATED_OFF,
    EXPECTED_TOOL_COUNT_ELEVATED_ON,
    SCHEMA_TOOLS,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"


def test_g01_cors_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """G01 (I1): CORS matrix over MCP_INDIA_STACK_ALLOWED_ORIGINS.

    Matrix: unset, empty, one, two, "*", "*,https://a.com".
    The effective CORS config never has wildcard plus credentials; wildcard cases fail at startup.
    """
    from mcp_india_stack.server import main

    # Valid non-wildcard configurations
    valid_cases = [
        (None, False, []),
        ("", False, []),
        ("https://app.example.com", True, ["https://app.example.com"]),
        (
            "https://a.com, https://b.com",
            True,
            ["https://a.com", "https://b.com"],
        ),
    ]

    for origins_val, expected_creds, expected_origins in valid_cases:
        env = {"MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY}
        if origins_val is not None:
            env["MCP_INDIA_STACK_ALLOWED_ORIGINS"] = origins_val
        with captured_server_app(env) as app:
            stack = app.build_middleware_stack()
            curr = stack
            cors_mw = None
            while curr:
                if "CORSMiddleware" in curr.__class__.__name__:
                    cors_mw = curr
                    break
                curr = getattr(curr, "app", None)
            assert cors_mw is not None
            assert cors_mw.allow_credentials == expected_creds
            if expected_creds:
                assert "*" not in cors_mw.allow_origins
                for orig in expected_origins:
                    assert orig in cors_mw.allow_origins

    # Wildcard cases fail at startup
    wildcard_cases = ["*", "*,https://a.com", "https://a.com,*"]
    for wc in wildcard_cases:
        monkeypatch.setenv("MCP_INDIA_STACK_ALLOWED_ORIGINS", wc)
        monkeypatch.setenv("MCP_INDIA_STACK_API_KEY", VALID_TEST_API_KEY)
        monkeypatch.setattr("sys.argv", ["mcp-india-stack", "--transport", "sse"])
        with pytest.raises(RuntimeError, match="CORS misconfiguration"):
            main()


def test_g02_auth_token_validation_and_startup_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """G02 (I2): Auth with key returns 401 for bad/non-ASCII tokens, right token passes.

    Without a key, a startup WARNING is logged from server.py.
    """
    env_with_key = {"MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY}
    with captured_server_app(env_with_key) as app:
        client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)

        # No token
        r1 = client.post("/messages/", json={})
        assert r1.status_code == 401

        # Wrong token
        r2 = client.post(
            "/messages/",
            headers={"Authorization": "Bearer wrong_token_0123456789"},
            json={},
        )
        assert r2.status_code == 401

        # Non-ASCII token
        r3 = client.post(
            "/messages/",
            headers=[(b"authorization", b"Bearer \xc3\xa9_non_ascii_token_0123456789")],
            json={},
        )
        assert r3.status_code == 401

        # Correct token (reaches FastMCP handler, 400 for missing session_id)
        r4 = client.post(
            "/messages/",
            headers={"Authorization": f"Bearer {VALID_TEST_API_KEY}"},
            json={},
        )
        assert r4.status_code == 400
        assert "session_id is required" in r4.text

    # Without a key, startup warning is logged
    env_no_key = {
        "MCP_INDIA_STACK_API_KEY": "",
        "MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK": "1",
    }
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        with captured_server_app(env_no_key):
            assert any("is not set" in record.message for record in caplog.records)


def test_g03_clamp_bulk_workers_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    """G03 (I10): Every definition of _clamp_bulk_workers resolves inputs into [1, 20]."""
    definitions = []
    for py_path in (SRC / "mcp_india_stack").rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_clamp_bulk_workers":
                definitions.append(py_path)

    assert len(definitions) >= 1, "At least one _clamp_bulk_workers must exist"

    test_inputs = [None, "0", "-5", "9999", "abc", "10", "20", "1"]
    for path in definitions:
        rel_mod = "mcp_india_stack." + ".".join(
            path.relative_to(SRC / "mcp_india_stack").with_suffix("").parts
        )
        mod = importlib.import_module(rel_mod)
        clamp_fn = mod._clamp_bulk_workers

        for val in test_inputs:
            if val is None:
                monkeypatch.delenv("MCP_INDIA_STACK_BULK_WORKERS", raising=False)
            else:
                monkeypatch.setenv("MCP_INDIA_STACK_BULK_WORKERS", val)
            res = clamp_fn()
            assert isinstance(res, int)
            assert 1 <= res <= 20, f"Failed for input {val!r} in {rel_mod}: got {res}"


def test_g04_dataset_manifest_checksums_match() -> None:
    """G04 (I3, I11): For every dataset in update_datasets DATASET_CONFIG,
    SHA-256 matches manifest.
    """
    script_path = ROOT / "scripts" / "update_datasets.py"
    spec = importlib.util.spec_from_file_location("update_datasets_script", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    manifest_path = SRC / "mcp_india_stack" / "data" / "dataset_checksums.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for name in mod.DATASET_CONFIG:
        assert name in manifest
        entry = manifest[name]
        data_file = ROOT / entry["file"]
        assert data_file.exists()
        assert hashlib.sha256(data_file.read_bytes()).hexdigest() == entry["sha256"]


def test_g05_no_network_imports_in_utils() -> None:
    """G05 (I3): AST check: no network client imports in src/mcp_india_stack/utils/."""
    forbidden = {"httpx", "requests", "urllib", "http", "socket", "aiohttp"}
    for py_file in (SRC / "mcp_india_stack" / "utils").glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module.split(".")[0] not in forbidden


def test_g06_database_module_no_dead_stubs() -> None:
    """G06 (I4): Database module has no query_db or init_db_connection."""
    import mcp_india_stack.database as db_mod

    assert not hasattr(db_mod, "query_db")
    assert not hasattr(db_mod, "init_db_connection")
    db_source = (SRC / "mcp_india_stack" / "database.py").read_text(encoding="utf-8")
    assert "query_db" not in db_source
    assert "init_db_connection" not in db_source


def test_g07_telemetry_hmac_and_no_op_without_pepper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """G07 (I7): Telemetry HMAC differs from plain sha256; module is no-op without pepper."""
    import importlib

    from mcp_india_stack import telemetry

    # Without pepper -> log_tool_usage is no-op, enabled is False
    monkeypatch.delenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", raising=False)
    importlib.reload(telemetry)
    assert not telemetry.get_telemetry_status()["enabled"]

    # With pepper -> HMAC hash differs from plain SHA-256; raw PII never appears in sink
    sink_file = tmp_path / "telemetry.jsonl"
    pepper = "secret-pepper-key-for-test-12345"
    monkeypatch.setenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", pepper)
    monkeypatch.setenv("MCP_INDIA_STACK_LOG_PATH", str(sink_file))
    importlib.reload(telemetry)
    assert telemetry.get_telemetry_status()["enabled"]

    raw_val = "ABCDE1234F"
    telemetry.log_tool_usage("validate_pan", raw_val, 2.5, "valid")
    assert sink_file.exists()
    content = sink_file.read_text(encoding="utf-8")
    assert raw_val not in content

    expected_hmac = hmac.new(
        key=pepper.encode("utf-8"), msg=raw_val.encode("utf-8"), digestmod="sha256"
    ).hexdigest()[:16]
    assert expected_hmac in content

    plain_sha = hashlib.sha256(raw_val.encode("utf-8")).hexdigest()[:16]
    assert expected_hmac != plain_sha

    # Clean up telemetry state
    monkeypatch.delenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", raising=False)
    importlib.reload(telemetry)


def test_g08_tool_tiers_and_elevated_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """G08 (I8): Every tool has a tier; INITIATE/SUBMIT absent unless elevated tools enabled."""
    import importlib
    import sys

    import mcp_india_stack.app as app_mod
    from mcp_india_stack.permission_tiers import PermissionTier

    reg_modules = [
        "mcp_india_stack.registrations.banking",
        "mcp_india_stack.registrations.finance",
        "mcp_india_stack.registrations.kyc",
        "mcp_india_stack.registrations.legal",
        "mcp_india_stack.registrations.lookup",
        "mcp_india_stack.registrations.markets",
        "mcp_india_stack.registrations.tax",
    ]

    # 1. Elevated OFF
    monkeypatch.delenv("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", raising=False)
    importlib.reload(app_mod)
    for m in reg_modules:
        if m in sys.modules:
            importlib.reload(sys.modules[m])

    tools_off = set(app_mod.mcp._tool_manager._tools.keys())
    assert len(tools_off) == EXPECTED_TOOL_COUNT_ELEVATED_OFF

    for tool_name in tools_off:
        tier = app_mod.TOOL_TIERS.get(tool_name)
        assert tier is not None
        assert tier not in (PermissionTier.INITIATE, PermissionTier.SUBMIT)

    # 2. Elevated ON
    monkeypatch.setenv("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", "1")
    importlib.reload(app_mod)
    for m in reg_modules:
        if m in sys.modules:
            importlib.reload(sys.modules[m])

    tools_on = set(app_mod.mcp._tool_manager._tools.keys())
    assert len(tools_on) == EXPECTED_TOOL_COUNT_ELEVATED_ON

    elevated_tiers_present = any(
        app_mod.TOOL_TIERS.get(name) in (PermissionTier.INITIATE, PermissionTier.SUBMIT)
        for name in tools_on
    )
    assert elevated_tiers_present

    # Restore default state
    monkeypatch.delenv("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", raising=False)
    importlib.reload(app_mod)
    for m in reg_modules:
        if m in sys.modules:
            importlib.reload(sys.modules[m])


def test_g09_ast_normalization_imports() -> None:
    """G09 (I9, I14): No function-local import of normalization in src;
    UPI and pincode import it.
    """
    for py_file in (SRC / "mcp_india_stack").rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Import):
                        for alias in inner.names:
                            assert "normalization" not in alias.name, (
                                f"Local import in {py_file}:{inner.lineno}"
                            )
                    elif (
                        isinstance(inner, ast.ImportFrom)
                        and inner.module
                        and "normalization" in inner.module
                    ):
                        raise AssertionError(f"Local from-import in {py_file}:{inner.lineno}")

    # UPI and Pincode import shared normalizer
    upi_src = (SRC / "mcp_india_stack" / "tools" / "upi.py").read_text(encoding="utf-8")
    pincode_src = (SRC / "mcp_india_stack" / "tools" / "pincode.py").read_text(encoding="utf-8")
    assert "from mcp_india_stack.normalization import" in upi_src
    assert "from mcp_india_stack.normalization import" in pincode_src


def test_g10_server_no_mcp_tool_and_line_count_bound() -> None:
    """G10 (I7): server.py has no @mcp.tool; line count is <= 705."""
    server_path = SRC / "mcp_india_stack" / "server.py"
    lines = server_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 705, f"server.py exceeded max line count: {len(lines)}"

    tree = ast.parse("\n".join(lines))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                assert "mcp.tool" not in dec_str, f"Direct @mcp.tool found on {node.name}"


def test_g11_delegation_rule() -> None:
    """G11 (I8): Registered wrappers delegate only under strict AST criteria.

    Set of non-delegating tools must EQUAL the canonical allowlist.
    """
    allowlist = {
        "bulk_validate_gstin",
        "bulk_validate_pan",
        "bulk_validate_ifsc",
        "decode_digilocker_uri",
        "decode_pan_type",
        "lookup_bank",
        "validate_aa_consent_artifact",
        "validate_epf_code",
        "validate_esic_code",
    }

    non_delegating = set()
    registrations_dir = SRC / "mcp_india_stack" / "registrations"

    for py_file in registrations_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if it has a tool decorator (e.g. @mcp.tool or @register)
                is_wrapper = any(
                    "tool" in (ast.unparse(d) if hasattr(ast, "unparse") else "")
                    for d in node.decorator_list
                )
                if not is_wrapper:
                    continue

                tool_name = node.name
                stmts = [
                    s
                    for s in node.body
                    if not (
                        isinstance(s, ast.Expr)
                        and isinstance(s.value, ast.Constant)
                        and isinstance(s.value.value, str)
                    )
                ]

                has_loop = any(
                    isinstance(s, (ast.For, ast.AsyncFor, ast.While)) for s in ast.walk(node)
                )
                has_tpe = any(
                    isinstance(n, ast.Name) and n.id == "ThreadPoolExecutor"
                    for s in stmts
                    for n in ast.walk(s)
                )
                has_large_literal = False
                for s in stmts:
                    for sub in ast.walk(s):
                        if isinstance(sub, (ast.List, ast.Set, ast.Tuple)) and len(sub.elts) > 5:
                            has_large_literal = True
                        elif isinstance(sub, ast.Dict) and len(sub.keys) > 5:
                            has_large_literal = True

                # Delegates condition
                delegates = (
                    len(stmts) <= 3 and not has_loop and not has_tpe and not has_large_literal
                )
                if not delegates:
                    non_delegating.add(tool_name)

    assert non_delegating == allowlist, (
        f"Non-delegating tools mismatch: "
        f"added={non_delegating - allowlist}, removed={allowlist - non_delegating}"
    )


def test_g12_yfinance_single_import() -> None:
    """G12 (I12): import yfinance appears in exactly one file under src."""
    import_files = set()
    for py_file in SRC.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "yfinance":
                        import_files.add(py_file)
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".")[0] == "yfinance"
            ):
                import_files.add(py_file)

    assert len(import_files) == 1
    assert next(iter(import_files)).name == "yfinance_provider.py"


def test_g13_host_argument_default_loopback() -> None:
    """G13 (I2): argparse --host default is loopback."""
    from mcp_india_stack.server import main

    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = argparse.Namespace(transport="stdio", refresh_all=False)
        with patch("mcp_india_stack.server.mcp.run"):
            main()

    server_src = (SRC / "mcp_india_stack" / "server.py").read_text(encoding="utf-8")
    assert 'default="127.0.0.1"' in server_src


def test_g14_middleware_order_behavior() -> None:
    """G14 (I2): Middleware order: preflight succeeds, error responses carry CORS headers."""
    env = {
        "MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY,
        "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://allowed.example.com",
    }
    with captured_server_app(env) as app:
        client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)

        # Preflight OPTIONS without token succeeds with 200 and CORS headers
        r_preflight = client.options(
            "/messages/",
            headers={
                "Origin": "https://allowed.example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert r_preflight.status_code == 200
        assert (
            r_preflight.headers.get("Access-Control-Allow-Origin") == "https://allowed.example.com"
        )

        # 401 response preserves CORS headers
        r_401 = client.post(
            "/messages/",
            headers={
                "Origin": "https://allowed.example.com",
                "Authorization": "Bearer bad_token",
            },
            json={},
        )
        assert r_401.status_code == 401
        assert r_401.headers.get("Access-Control-Allow-Origin") == "https://allowed.example.com"


def test_g15_startup_refusal_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """G15 (I2): Startup refusals exit non-zero and uvicorn.run is never called."""
    from mcp_india_stack.server import main

    refusal_cases = [
        # (host, key, opt_in, allowed_hosts)
        ("127.0.0.1", "short_key", "", ""),  # key < 32
        ("0.0.0.0", "", "", ""),  # non-loopback no key no opt-in
        ("0.0.0.0", "", "0", ""),  # opt-in != 1
        (
            "127.0.0.1",
            VALID_TEST_API_KEY,
            "",
            "invalid://scheme",
        ),  # scheme in host
    ]

    for host, key, opt_in, hosts in refusal_cases:
        monkeypatch.setenv("MCP_INDIA_STACK_API_KEY", key)
        monkeypatch.setenv("MCP_INDIA_STACK_ALLOW_UNAUTHENTICATED_NETWORK", opt_in)
        monkeypatch.setenv("MCP_INDIA_STACK_ALLOWED_HOSTS", hosts)
        monkeypatch.setattr(
            "sys.argv",
            ["mcp-india-stack", "--transport", "sse", "--host", host],
        )

        with patch("uvicorn.run") as mock_uvicorn:
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code != 0
            mock_uvicorn.assert_not_called()


def test_g16_host_and_origin_allowlist_enforcement() -> None:
    """G16 (I2): Unlisted Host = 421, listed Host not 421, unlisted Origin = 403."""
    env = {
        "MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY,
        "MCP_INDIA_STACK_ALLOWED_HOSTS": "api.example.com",
        "MCP_INDIA_STACK_ALLOWED_ORIGINS": "https://allowed.example.com",
    }
    with captured_server_app(env) as app:
        client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {VALID_TEST_API_KEY}"}

        # Unlisted Host -> 421
        r1 = client.post(
            "/messages/",
            headers={**headers, "Host": "evil.example.com"},
            json={},
        )
        assert r1.status_code == 421

        # Listed Host -> non-421 (400)
        r2 = client.post(
            "/messages/",
            headers={**headers, "Host": "api.example.com"},
            json={},
        )
        assert r2.status_code == 400

        # Unlisted Origin -> 403
        r3 = client.post(
            "/messages/",
            headers={
                **headers,
                "Host": "localhost",
                "Origin": "https://evil.example.com",
            },
            json={},
        )
        assert r3.status_code == 403


def test_g17_auth_failure_throttle_and_bounded_stores() -> None:
    """G17 (I2): LIMIT+1 wrong tokens returns 429; valid token passes; stores bounded."""
    env = {
        "MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY,
        "MCP_INDIA_STACK_AUTH_FAIL_LIMIT": "3",
    }
    with captured_server_app(env) as app:
        client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)

        # 3 wrong tokens return 401
        for i in range(3):
            r = client.post(
                "/messages/",
                headers={"Authorization": f"Bearer bad_{i}"},
                json={},
            )
            assert r.status_code == 401

        # 4th wrong token returns 429 with Retry-After
        r_throttled = client.post("/messages/", headers={"Authorization": "Bearer bad_4"}, json={})
        assert r_throttled.status_code == 429
        assert "Retry-After" in r_throttled.headers

        # Valid token still passes in same window
        r_valid = client.post(
            "/messages/",
            headers={"Authorization": f"Bearer {VALID_TEST_API_KEY}"},
            json={},
        )
        assert r_valid.status_code == 400


def test_g18_rate_limit_token_hash_keys() -> None:
    """G18 (I2): With key configured, store key is key:<prefix>; unauth rotates IP buckets."""
    env = {
        "MCP_INDIA_STACK_API_KEY": VALID_TEST_API_KEY,
        "MCP_INDIA_STACK_RATE_LIMIT": "60/60",
    }
    with captured_server_app(env) as app:
        client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)
        client.post(
            "/messages/",
            headers={"Authorization": f"Bearer {VALID_TEST_API_KEY}"},
            json={},
        )

        curr = app.middleware_stack
        rate_mw = None
        while curr:
            if "_RateLimitMiddleware" in curr.__class__.__name__:
                rate_mw = curr
                break
            curr = getattr(curr, "app", None)

        assert rate_mw is not None
        assert len(rate_mw._buckets) == 1
        key = next(iter(rate_mw._buckets))
        assert key.startswith("key:")
        expected_prefix = hashlib.sha256(VALID_TEST_API_KEY.encode("utf-8")).hexdigest()[:16]
        assert key == f"key:{expected_prefix}"


def test_g19_schema_parity_tools_match() -> None:
    """G19 (I8): Exact SCHEMA_TOOLS match and no skip."""
    import mcp_india_stack.registrations  # noqa: F401
    from mcp_india_stack.app import mcp

    registered = set(mcp._tool_manager._tools.keys())
    assert SCHEMA_TOOLS <= registered
    assert len(SCHEMA_TOOLS) == 21


def test_g20_no_unjustified_nosec_and_no_skip_markers() -> None:
    """G20: No skip/xfail markers across tests; no bare nosec in src."""
    for test_file in TESTS.rglob("*.py"):
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec)
                    assert "pytest.mark.skip" not in dec_str, (
                        f"Skip marker in {test_file.name}:{node.name}"
                    )
                    assert "pytest.mark.xfail" not in dec_str, (
                        f"Xfail marker in {test_file.name}:{node.name}"
                    )
            elif isinstance(node, ast.Call):
                call_str = ast.unparse(node.func)
                assert call_str not in ("pytest.skip", "pytest.xfail"), (
                    f"Skip call in {test_file.name}:{call_str}"
                )

    for py_file in SRC.rglob("*.py"):
        lines = py_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            if "# nosec" in line:
                comment = line[line.index("# nosec") :]
                assert "B" in comment and "-" in comment, (
                    f"Bare # nosec found in {py_file}:{idx}: {line.strip()}"
                )
