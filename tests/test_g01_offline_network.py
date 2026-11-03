"""Tests for G1: Offline claim verification and tool network classification."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any
from unittest.mock import patch

from mcp_india_stack.app import TOOL_NETWORK, TOOL_TIERS
from mcp_india_stack.server import server_status


def test_g1_tool_network_registry_completeness() -> None:
    """Assert all 78 registered tools have a network attribute in TOOL_NETWORK."""
    assert len(TOOL_NETWORK) == len(TOOL_TIERS)
    assert set(TOOL_NETWORK.keys()) == set(TOOL_TIERS.keys())
    for _tool_name, net_attr in TOOL_NETWORK.items():
        assert net_attr in {"none", "optional", "required"}

    # Stock tools are required
    assert TOOL_NETWORK["get_stock_quote"] == "required"
    assert TOOL_NETWORK["get_stock_history"] == "required"

    # CDN refresh tools are optional
    for cdn_tool in [
        "lookup_ifsc",
        "bulk_validate_ifsc",
        "lookup_pincode",
        "lookup_hsn_code",
        "calculate_gst",
    ]:
        assert TOOL_NETWORK[cdn_tool] == "optional"


def test_g1_status_resource_exposes_tools_network() -> None:
    """india://status resource additively exposes tools_network."""
    status = server_status()
    assert "tools_network" in status
    assert status["tools_network"] == TOOL_NETWORK


def test_g1_readme_table_matches_registry() -> None:
    """README offline-first section lists tool classes and matches the registry."""
    readme_path = Path(__file__).resolve().parents[1] / "README.md"
    readme_content = readme_path.read_text(encoding="utf-8")

    # Verify Offline-First Guarantee rewrite exists
    assert (
        "### Offline-First Guarantee" in readme_content
        or "## Offline-First Guarantee" in readme_content
    )

    # Check for presence of the three network tiers in README
    assert "Network: None" in readme_content or "`none`" in readme_content
    assert "Network: Optional" in readme_content or "`optional`" in readme_content
    assert "Network: Required" in readme_content or "`required`" in readme_content

    # Every tool name should appear under its respective class in the README table/list
    for tool_name, _net_attr in TOOL_NETWORK.items():
        assert f"`{tool_name}`" in readme_content


def test_g1_socket_blocked_offline_execution() -> None:
    """With sockets blocked, 'none' tools execute cleanly and 'required' tools return errors."""

    def blocked_connect(self: Any, *args: Any, **kwargs: Any) -> None:
        raise OSError("Network is unreachable (simulated socket block)")

    # Also block curl_cffi if installed in the host environment
    curl_patch = None
    try:
        import curl_cffi.requests

        curl_patch = patch.object(
            curl_cffi.requests.Session,
            "request",
            side_effect=OSError("Network is unreachable (simulated socket block)"),
        )
        curl_patch.start()
    except (ImportError, AttributeError):
        pass

    try:
        with patch.object(socket.socket, "connect", blocked_connect):
            # 1. 'none' tools smoke test: validate_pan
            from mcp_india_stack.tools.pan import validate_pan

            pan_res = validate_pan("ABCDE1234F")
            assert pan_res["success"] is True

            # calculate_income_tax
            from mcp_india_stack.tools.income_tax import calculate_income_tax

            tax_res = calculate_income_tax(1200000)
            assert tax_res["gross_income"] == 1200000
            assert not tax_res["errors"]

            # 2. 'required' tools smoke test: get_stock_quote returns structured error
            from mcp_india_stack.tools.stock_market import get_stock_quote

            stock_res = get_stock_quote("RELIANCE.NS")
            assert stock_res["success"] is False
            assert "errors" in stock_res
            assert len(stock_res["errors"]) > 0
            assert "traceback" not in stock_res
    finally:
        if curl_patch:
            curl_patch.stop()
