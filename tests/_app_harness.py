"""Test harness for capturing and exercising the real ASGI app from server.main()."""

from __future__ import annotations

import copy
import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from starlette.types import ASGIApp

import mcp_india_stack.server as server_module
from mcp_india_stack.app import mcp

VALID_TEST_API_KEY = "test_secret_api_key_must_be_32_chars_or_more_ok"


@contextmanager
def captured_server_app(
    env: dict[str, str] | None = None,
    argv: list[str] | None = None,
) -> Generator[ASGIApp, None, None]:
    """Capture the Starlette SSE application constructed by server.main().

    Restores os.environ and mcp.settings.transport_security upon exit.
    """
    orig_env = dict(os.environ)
    orig_transport_sec = copy.deepcopy(mcp.settings.transport_security)
    captured: list[ASGIApp] = []

    def fake_uvicorn_run(app: ASGIApp, **kwargs: Any) -> None:
        captured.append(app)

    if env is not None:
        os.environ.clear()
        os.environ.update(orig_env)
        os.environ.update(env)

    call_argv = argv if argv is not None else ["mcp-india-stack", "--transport", "sse"]

    try:
        with patch.object(sys, "argv", call_argv):
            with patch("uvicorn.run", side_effect=fake_uvicorn_run):
                server_module.main()

        if not captured:
            raise RuntimeError("uvicorn.run was not called; app not captured")
        yield captured[0]
    finally:
        os.environ.clear()
        os.environ.update(orig_env)
        mcp.settings.transport_security = orig_transport_sec
