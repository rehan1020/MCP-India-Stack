import importlib

import pytest

from mcp_india_stack.permission_tiers import PermissionTier


def test_all_tools_classified():
    # We must ensure server.py classifies all tools.
    # The classification dictionary is at the top of server.py
    from mcp_india_stack import server

    # We can inspect mcp.tools to see if any are missing from TOOL_TIERS,
    # but the decorator already raises an error if it's missing!
    # Let's verify no tools were missed in TOOL_TIERS manually or if server loaded successfully.

    assert hasattr(server, "TOOL_TIERS")
    assert len(server.TOOL_TIERS) == 78

    # Check that elevated tools are omitted when elevated is disabled
    # default in tests is elevated disabled
    elevated = [
        k
        for k, v in server.TOOL_TIERS.items()
        if v in (PermissionTier.INITIATE, PermissionTier.SUBMIT)
    ]

    # Verify these elevated tools are NOT in the fastmcp instance
    registered_tools = [t for t in server.mcp._tool_manager._tools]
    for t in elevated:
        assert t not in registered_tools


def test_missing_classification_raises_error(monkeypatch):
    from mcp_india_stack import server

    monkeypatch.delitem(server.TOOL_TIERS, "lookup_ifsc", raising=False)

    with pytest.raises(RuntimeError, match="lacks a PermissionTier classification"):

        @server._wrapped_mcp_tool()
        def lookup_ifsc():
            pass


def test_elevated_gating(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", "1")
    # We must reload server module to re-evaluate the env var
    import mcp_india_stack.server as server

    importlib.reload(server)

    elevated = [
        k
        for k, v in server.TOOL_TIERS.items()
        if v in (PermissionTier.INITIATE, PermissionTier.SUBMIT)
    ]
    registered_tools = [t for t in server.mcp._tool_manager._tools]

    for t in elevated:
        assert t in registered_tools
