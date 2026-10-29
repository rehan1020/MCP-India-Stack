"""Smoke test for installed mcp-india-stack wheel package."""

from __future__ import annotations

import argparse
import asyncio
import importlib.resources
import os
import runpy
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


async def check_stdio_tools(expected_off: int, expected_on: int) -> None:
    """Check tool count via MCP client over stdio."""
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    for elevated, expected in [(False, expected_off), (True, expected_on)]:
        env = os.environ.copy()
        if elevated:
            env["MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS"] = "true"
        else:
            env.pop("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", None)

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_india_stack", "--transport", "stdio"],
            env=env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_res = await session.list_tools()
                count = len(tools_res.tools)
                if count != expected:
                    raise AssertionError(
                        f"Expected {expected} tools (elevated={elevated}), got {count}"
                    )
        print(f"stdio tools (elevated={elevated}): {count} matches expected {expected}")


def check_sse_server() -> None:
    """Check real SSE server on loopback with API key and ALLOWED_HOSTS."""
    port = 18088
    api_key = "test-secret-key-at-least-32-chars-long-01234"
    env = os.environ.copy()
    env["MCP_INDIA_STACK_API_KEY"] = api_key
    env["MCP_INDIA_STACK_ALLOWED_HOSTS"] = "localhost,127.0.0.1"

    cmd = [
        sys.executable,
        "-m",
        "mcp_india_stack",
        "--transport",
        "sse",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait up to 10 seconds for server to bind
        url = f"http://127.0.0.1:{port}/messages/"
        started = False
        for _ in range(20):
            try:
                req = urllib.request.Request(url, data=b"{}", method="POST")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    pass
            except urllib.error.HTTPError as exc:
                if exc.code in (400, 401, 421):
                    started = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if not started:
            err_msg = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
            raise RuntimeError(
                f"SSE server did not start on port {port} in time. stderr: {err_msg}"
            )

        # 1. Without token -> 401
        req1 = urllib.request.Request(url, data=b"{}", method="POST")
        req1.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req1, timeout=2.0):
                raise AssertionError("Expected 401 Unauthorized without token")
        except urllib.error.HTTPError as exc:
            assert exc.code == 401, f"Expected 401, got {exc.code}"

        # 2. Allowed Host with token -> non-421 (400)
        req2 = urllib.request.Request(url, data=b"{}", method="POST")
        req2.add_header("Content-Type", "application/json")
        req2.add_header("Authorization", f"Bearer {api_key}")
        req2.add_header("Host", f"127.0.0.1:{port}")
        try:
            with urllib.request.urlopen(req2, timeout=2.0) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        assert status != 421, f"Expected non-421 for allowed host, got {status}"
        assert status == 400, f"Expected 400 for missing session_id, got {status}"

        # 3. Disallowed Host with token -> 421
        req3 = urllib.request.Request(url, data=b"{}", method="POST")
        req3.add_header("Content-Type", "application/json")
        req3.add_header("Authorization", f"Bearer {api_key}")
        req3.add_header("Host", "disallowed.example.com")
        try:
            with urllib.request.urlopen(req3, timeout=2.0):
                raise AssertionError("Expected 421 Misdirected Request for disallowed host")
        except urllib.error.HTTPError as exc:
            assert exc.code == 421, f"Expected 421, got {exc.code}"

        print(
            "SSE server checks passed: 401 without token, non-421 allowed host, 421 disallowed host"
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test wheel installation")
    parser.add_argument("--constants", type=Path, required=True, help="Path to tests/constants.py")
    args = parser.parse_args()

    # 1. Read constants
    if not args.constants.exists():
        sys.stderr.write(f"Constants file {args.constants} does not exist\n")
        sys.exit(1)

    constants = runpy.run_path(str(args.constants))
    expected_off = constants["EXPECTED_TOOL_COUNT_ELEVATED_OFF"]
    expected_on = constants["EXPECTED_TOOL_COUNT_ELEVATED_ON"]

    # 2. Verify import
    import mcp_india_stack

    print(f"Imported mcp_india_stack from {mcp_india_stack.__file__}")

    # 3. Verify packaged manifest and datasets exist
    ref = importlib.resources.files("mcp_india_stack")
    data_dir = ref / "data"
    assert (data_dir / "dataset_checksums.json").is_file(), "Manifest missing"
    assert (data_dir / "ifsc" / "IFSC.csv").is_file(), "IFSC dataset missing"
    assert (data_dir / "pincode" / "pincode.csv.gz").is_file(), "Pincode dataset missing"
    assert (data_dir / "hsn" / "hsn_master.csv").is_file(), "HSN dataset missing"
    print("Runtime packaged manifest and dataset files exist.")

    # 4. Check stdio tools
    asyncio.run(check_stdio_tools(expected_off, expected_on))

    # 5. Check SSE server
    check_sse_server()

    print("ALL WHEEL SMOKE CHECKS PASSED.")


if __name__ == "__main__":
    main()
