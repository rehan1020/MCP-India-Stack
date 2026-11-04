"""End-to-end tests for remote SSE transport (G10).

Validates:
- Ephemeral loopback port binding
- Unauthenticated /health, /healthz, and / routes
- Bearer token authentication (ok, missing, wrong)
- FastMCP tool invocation over SSE using official MCP client
- 20 concurrent clients
- Malformed JSON-RPC handling (400)
- Oversized payload rejection (413)
- Mid-call client disconnect resilience
- Rate limiting trip (429)
- Clean, graceful shutdown
"""

from __future__ import annotations

import asyncio
import os
import socket
import threading
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from mcp_india_stack import __version__
from mcp_india_stack.server import create_sse_app

TEST_API_KEY = "test_secret_api_key_must_be_32_chars_or_more_ok"


def get_free_port() -> int:
    """Find an available ephemeral port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def sse_server() -> Generator[tuple[str, int, uvicorn.Server], None, None]:
    """Start an ephemeral SSE server with default test configuration."""
    port = get_free_port()
    orig_env = dict(os.environ)
    os.environ["MCP_INDIA_STACK_API_KEY"] = TEST_API_KEY
    os.environ["MCP_INDIA_STACK_RATE_LIMIT"] = "100/60"

    app, host, _ = create_sse_app("127.0.0.1", port)
    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server readiness
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            r = httpx.get(f"{url}/health", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.05)

    try:
        yield url, port, server
    finally:
        server.should_exit = True
        thread.join(timeout=3.0)
        os.environ.clear()
        os.environ.update(orig_env)


def test_sse_health_and_root_endpoints(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """Unauthenticated health and root endpoints respond with 200 OK and valid JSON."""
    url, _, _ = sse_server

    r_health = httpx.get(f"{url}/health")
    assert r_health.status_code == 200
    assert r_health.json() == {"status": "ok", "version": __version__}

    r_healthz = httpx.get(f"{url}/healthz")
    assert r_healthz.status_code == 200
    assert r_healthz.json() == {"status": "ok", "version": __version__}

    r_root = httpx.get(f"{url}/")
    assert r_root.status_code == 200
    assert r_root.json() == {
        "status": "ok",
        "service": "mcp-india-stack",
        "version": __version__,
    }


def test_sse_auth_missing_and_wrong(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """Missing or invalid Bearer tokens are rejected with 401 Unauthorized."""
    url, _, _ = sse_server

    # Missing auth on SSE stream
    r1 = httpx.get(f"{url}/sse")
    assert r1.status_code == 401
    assert r1.json() == {"error": "Unauthorized"}

    # Wrong auth token on SSE stream
    r2 = httpx.get(f"{url}/sse", headers={"Authorization": "Bearer wrong_token_value_here"})
    assert r2.status_code == 401
    assert r2.json() == {"error": "Unauthorized"}

    # Missing auth on POST messages
    r3 = httpx.post(f"{url}/messages/")
    assert r3.status_code == 401

    # Wrong auth on POST messages
    r4 = httpx.post(
        f"{url}/messages/",
        headers={"Authorization": "Bearer wrong_token_value_here"},
    )
    assert r4.status_code == 401


def test_sse_auth_ok_and_tool_call(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """Valid Bearer token allows SSE connection and tool invocation via MCP client."""
    url, _, _ = sse_server

    async def _exercise_mcp_client() -> None:
        sse_url = f"{url}/sse"
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}

        async with sse_client(sse_url, headers=headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                init_res = await session.initialize()
                assert init_res is not None

                # List tools (74 standard tools bundled; 78 when elevated is enabled)
                tools_res = await session.list_tools()
                assert len(tools_res.tools) >= 74

                # Call tool
                call_res = await session.call_tool("validate_pan", {"pan": "AAPFU0939F"})
                assert call_res is not None
                assert call_res.isError is False
                assert len(call_res.content) > 0
                assert "valid" in call_res.content[0].text

    asyncio.run(_exercise_mcp_client())


def test_sse_20_concurrent_clients(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """20 concurrent clients make simultaneous requests without errors or deadlocks."""
    url, _, _ = sse_server

    def _client_request(idx: int) -> int:
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        # Concurrently query health and server status
        resp = httpx.get(f"{url}/health", timeout=5.0)
        assert resp.status_code == 200

        # Also make an authenticated request
        resp_auth = httpx.post(f"{url}/messages/", headers=headers, json={}, timeout=5.0)
        # FastMCP returns 400 for empty body, proving auth passed
        assert resp_auth.status_code == 400
        return resp.status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(_client_request, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert len(results) == 20
    assert all(code == 200 for code in results)


def test_sse_malformed_json_rpc(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """Malformed JSON-RPC or corrupt JSON payloads return HTTP 400 Bad Request."""
    url, _, _ = sse_server
    headers = {
        "Authorization": f"Bearer {TEST_API_KEY}",
        "Content-Type": "application/json",
    }

    # Malformed JSON syntax
    r1 = httpx.post(
        f"{url}/messages/?session_id=any",
        headers=headers,
        content=b'{"broken_json: incomplete',
    )
    assert r1.status_code == 400

    # Non-JSON payload
    r2 = httpx.post(
        f"{url}/messages/?session_id=any",
        headers=headers,
        content=b"not-json-text",
    )
    assert r2.status_code == 400


def test_sse_oversized_body() -> None:
    """Payloads exceeding MCP_INDIA_STACK_MAX_BODY_SIZE return HTTP 413."""
    port = get_free_port()
    orig_env = dict(os.environ)
    os.environ["MCP_INDIA_STACK_API_KEY"] = TEST_API_KEY
    os.environ["MCP_INDIA_STACK_MAX_BODY_SIZE"] = "2048"

    app, host, _ = create_sse_app("127.0.0.1", port)
    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            if httpx.get(f"{url}/health").status_code == 200:
                break
        except Exception:
            time.sleep(0.05)

    try:
        headers = {
            "Authorization": f"Bearer {TEST_API_KEY}",
            "Content-Type": "application/json",
        }
        # Oversized payload (> 2048 bytes)
        big_payload = b"x" * 4096
        r_large = httpx.post(f"{url}/messages/", headers=headers, content=big_payload)
        assert r_large.status_code == 413
        assert r_large.json() == {"error": "Payload too large"}

        # Normal sized payload (<= 2048 bytes)
        small_payload = b"{}"
        r_small = httpx.post(f"{url}/messages/", headers=headers, content=small_payload)
        assert r_small.status_code != 413
    finally:
        server.should_exit = True
        thread.join(timeout=3.0)
        os.environ.clear()
        os.environ.update(orig_env)


def test_sse_mid_call_disconnect(sse_server: tuple[str, int, uvicorn.Server]) -> None:
    """Server handles unexpected client disconnect without crashing or hanging."""
    url, port, _ = sse_server

    # Connect raw TCP socket and send partial SSE request, then abruptly close
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    req = (
        f"GET /sse HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        f"Authorization: Bearer {TEST_API_KEY}\r\n"
        f"Accept: text/event-stream\r\n\r\n"
    )
    s.sendall(req.encode("utf-8"))
    # Read response status line
    res = s.recv(100)
    assert b"200" in res

    # Abruptly close socket
    s.close()
    time.sleep(0.1)

    # Verify server is completely healthy and responsive
    r_check = httpx.get(f"{url}/health")
    assert r_check.status_code == 200


def test_sse_rate_limit_trip() -> None:
    """Exceeding MCP_INDIA_STACK_RATE_LIMIT returns HTTP 429 Too Many Requests."""
    port = get_free_port()
    orig_env = dict(os.environ)
    os.environ["MCP_INDIA_STACK_API_KEY"] = TEST_API_KEY
    os.environ["MCP_INDIA_STACK_RATE_LIMIT"] = "5/60"

    app, host, _ = create_sse_app("127.0.0.1", port)
    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            if httpx.get(f"{url}/health").status_code == 200:
                break
        except Exception:
            time.sleep(0.05)

    try:
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        # Make 5 requests within window
        for _ in range(5):
            r = httpx.post(f"{url}/messages/", headers=headers, json={})
            assert r.status_code in (400, 200, 202)

        # 6th request trips the limit
        r_tripped = httpx.post(f"{url}/messages/", headers=headers, json={})
        assert r_tripped.status_code == 429
        assert r_tripped.json() == {"error": "Rate limit exceeded"}
    finally:
        server.should_exit = True
        thread.join(timeout=3.0)
        os.environ.clear()
        os.environ.update(orig_env)


def test_sse_graceful_shutdown() -> None:
    """Signaling server shutdown cleanly terminates background server thread."""
    port = get_free_port()
    orig_env = dict(os.environ)
    os.environ["MCP_INDIA_STACK_API_KEY"] = TEST_API_KEY

    app, host, _ = create_sse_app("127.0.0.1", port)
    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            if httpx.get(f"{url}/health").status_code == 200:
                break
        except Exception:
            time.sleep(0.05)

    assert thread.is_alive()

    # Trigger graceful shutdown
    server.should_exit = True
    thread.join(timeout=4.0)

    assert not thread.is_alive()
    # Connecting should now fail
    with pytest.raises((httpx.ConnectError, httpx.RequestError)):
        httpx.get(f"{url}/health", timeout=0.5)

    os.environ.clear()
    os.environ.update(orig_env)
