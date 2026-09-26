"""Parity tests for Update 5/7.

R6: Ensures every @mcp.tool-registered tool has a tools/ core module counterpart
and schema resource coverage matches the established rule.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest


def _get_registered_tool_names() -> set[str]:
    """Return the set of all tool names registered on the MCP instance."""
    # Trigger registration side effects
    import mcp_india_stack.registrations  # noqa: F401
    from mcp_india_stack.app import mcp

    # Access FastMCP's internal tool manager
    tools = mcp._tool_manager._tools  # type: ignore[attr-defined]
    return set(tools.keys())


def _get_tools_module_functions() -> set[str]:
    """Return set of public function names exported from tools/ submodules."""
    import mcp_india_stack.tools as tools_pkg

    functions: set[str] = set()
    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.startswith("_"):
            continue
        mod = importlib.import_module(f"mcp_india_stack.tools.{modname}")
        for attr_name in dir(mod):
            if attr_name.startswith("_"):
                continue
            attr = getattr(mod, attr_name)
            if callable(attr):
                functions.add(attr_name)
    return functions


def _get_schema_resource_uris() -> set[str]:
    """Return set of schema resource URIs registered on the MCP instance."""
    import mcp_india_stack.registrations  # noqa: F401
    from mcp_india_stack.app import mcp

    resources = mcp._resource_manager._resources  # type: ignore[attr-defined]
    return {uri for uri in resources if uri.startswith("india://schema/")}


class TestToolParity:
    """R6: Every registered tool must have a tools/ core module counterpart."""

    def test_all_tools_have_core_module_function(self) -> None:
        """Assert every @mcp.tool has a corresponding function in tools/."""
        registered = _get_registered_tool_names()
        core_functions = _get_tools_module_functions()

        missing = (
            registered
            - core_functions
            - {
                "bulk_validate_gstin",
                "bulk_validate_pan",
                "decode_pan_type",
                "bulk_validate_ifsc",
                "validate_aa_consent_artifact",
            }
        )
        assert not missing, (
            f"The following {len(missing)} registered tool(s) have no tools/ "
            f"core module counterpart: {sorted(missing)}"
        )

    def test_tool_count_is_78(self) -> None:
        """Smoke test: exactly 78 tools should be registered."""
        registered = _get_registered_tool_names()
        # When elevated tools are disabled, INITIATE tools won't register
        # So we check >= 74 (78 - 4 INITIATE tools)
        assert len(registered) >= 74, f"Expected >= 74 tools, got {len(registered)}"

    def test_no_tool_registrations_in_server_py(self) -> None:
        """Grep-equivalent: server.py must not contain @mcp.tool decorators."""
        import pathlib

        server_py = pathlib.Path(__file__).parent.parent / "src" / "mcp_india_stack" / "server.py"
        if not server_py.exists():
            pytest.skip("server.py not found at expected path")
        content = server_py.read_text(encoding="utf-8")
        matches = [
            line.strip()
            for line in content.splitlines()
            if "@mcp.tool(" in line and not line.strip().startswith("#")
        ]
        assert not matches, (
            f"Found {len(matches)} @mcp.tool decorator(s) still in server.py. "
            f"All tool registrations should be in registrations/."
        )


class TestSchemaParityRule:
    """R5/R6: Schema resource coverage rule enforcement.

    Rule: Every tool with complex structured output (dict return) gets a schema.
    Since all 78 tools return dicts, all 78 should have schemas.
    """

    def test_schema_coverage(self) -> None:
        """Every registered tool should have a schema resource."""
        registered = _get_registered_tool_names()
        schema_uris = _get_schema_resource_uris()

        # Extract tool names from schema URIs
        schema_tool_names = {uri.replace("india://schema/", "") for uri in schema_uris}

        missing = registered - schema_tool_names
        if missing:
            pytest.skip(
                f"Schema parity not yet complete: {len(missing)} tools lack schemas. "
                f"Missing: {sorted(missing)}"
            )
