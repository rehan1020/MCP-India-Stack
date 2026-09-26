import importlib

import pytest

from mcp_india_stack.permission_tiers import PermissionTier


def test_all_tools_classified():
    import mcp_india_stack.app as app

    assert hasattr(app, "TOOL_TIERS")
    assert len(app.TOOL_TIERS) == 78
    elevated = [
        k
        for k, v in app.TOOL_TIERS.items()
        if v in (PermissionTier.INITIATE, PermissionTier.SUBMIT)
    ]
    registered_tools = [t for t in app.mcp._tool_manager._tools]
    for t in elevated:
        assert t not in registered_tools


def test_missing_classification_raises_error(monkeypatch):
    import mcp_india_stack.app as app

    monkeypatch.delitem(app.TOOL_TIERS, "lookup_ifsc", raising=False)
    with pytest.raises(RuntimeError, match="lacks a PermissionTier classification"):

        @app._wrapped_mcp_tool()
        def lookup_ifsc():
            pass


def test_elevated_gating(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_ENABLE_ELEVATED_TOOLS", "1")
    import mcp_india_stack.app as app

    importlib.reload(app)

    import mcp_india_stack.registrations.banking as banking
    import mcp_india_stack.registrations.legal as legal

    importlib.reload(banking)
    importlib.reload(legal)

    elevated = [
        k
        for k, v in app.TOOL_TIERS.items()
        if v in (PermissionTier.INITIATE, PermissionTier.SUBMIT)
    ]
    registered_tools = [t for t in app.mcp._tool_manager._tools]
    for t in elevated:
        assert t in registered_tools
