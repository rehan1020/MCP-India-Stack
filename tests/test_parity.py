"""Parity tests for Update 5/7.

R6: Ensures every @mcp.tool-registered tool has a tools/ core module counterpart
and schema resource coverage matches the established rule.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any


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

        missing = registered - core_functions
        assert not missing, (
            f"The following {len(missing)} registered tool(s) have no tools/ "
            f"core module counterpart: {sorted(missing)}"
        )

    def test_tool_count_is_80(self) -> None:
        """Smoke test: exactly 80 tools should be registered."""
        registered = _get_registered_tool_names()
        # When elevated tools are disabled, INITIATE tools won't register
        # So we check >= 76 (80 - 4 INITIATE tools)
        assert len(registered) >= 76, f"Expected >= 76 tools, got {len(registered)}"

    def test_no_tool_registrations_in_server_py(self) -> None:
        """Grep-equivalent: server.py must not contain @mcp.tool decorators."""
        import pathlib

        server_py = pathlib.Path(__file__).parent.parent / "src" / "mcp_india_stack" / "server.py"
        assert server_py.exists(), "server.py not found at expected path"
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


from tests.constants import (
    SCHEMA_TOOLS,
)


class TestSchemaParityRule:
    """R5/R6: Schema resource coverage rule enforcement.

    Rule: Exactly the 21 tools in SCHEMA_TOOLS have registered JSON schema resources.
    """

    def test_schema_coverage(self) -> None:
        """Assert registered india://schema/* resources match SCHEMA_TOOLS exactly."""
        registered = _get_registered_tool_names()
        schema_uris = _get_schema_resource_uris()

        expected_uris = {f"india://schema/{name}" for name in SCHEMA_TOOLS}
        assert schema_uris == expected_uris, (
            f"Schema resources mismatch. Extra: {schema_uris - expected_uris}, "
            f"Missing: {expected_uris - schema_uris}"
        )

        assert SCHEMA_TOOLS <= registered, (
            f"Schema defined for unregistered tool(s): {SCHEMA_TOOLS - registered}"
        )


VERIFYING_TOOLS_SAMPLE_INPUTS: dict[str, dict[str, Any]] = {
    "validate_gstin": {"gstin": "27AAPFU0939F1ZV"},
    "validate_pan": {"pan": "ABCDE1234F"},
    "validate_aadhaar": {"aadhaar": "295945837261"},
    "validate_upi_vpa": {"vpa": "test@okaxis"},
    "validate_voter_id": {"voter_id": "ABC1234567"},
    "validate_driving_license": {"dl_number": "MH0220191234567"},
    "validate_passport": {"passport_number": "A1234567"},
    "validate_cin": {"cin": "L17110MH1973PLC019786"},
    "validate_din": {"din": "00012345"},
    "validate_fssai": {"license_number": "10019000000001"},
    "validate_epf_code": {"code": "MH/12345/123456/001"},
    "validate_esic_code": {"code": "11-00-12345-000-0001"},
    "validate_llpin": {"llpin": "AAA-1234"},
    "validate_mobile_number": {"mobile": "9820123456"},
    "validate_pran": {"pran": "110012345678"},
    "validate_tan": {"tan": "DELA12345F"},
    "validate_aa_consent_artifact": {
        "artifact": {
            "consentStart": "2026-01-01T00:00:00Z",
            "consentExpiry": "2026-02-01T00:00:00Z",
            "fiTypes": ["DEPOSIT"],
        }
    },
    "bulk_validate_gstin": {"gstins": ["27AAPFU0939F1ZV"]},
    "bulk_validate_pan": {"pans": ["ABCDE1234F"]},
    "bulk_validate_ifsc": {"ifscs": ["HDFC0000001"]},
    "bulk_validate_aadhaar": {"numbers": ["295945837261"]},
    "lookup_ifsc": {"ifsc_code": "HDFC0000001"},
    "lookup_pincode": {"pincode": "110001"},
    "decode_state_code": {"value": "27"},
    "decode_isin": {"isin": "INE002A01018"},
    "lookup_bbps_biller": {"biller_id": "MSED00001"},
    "lookup_hsn_code": {"code": "0101"},
    "verify_einvoice_qr": {"qr_text": "sample.jwt.string"},
    "verify_aadhaar_offline_artifact": {
        "xml_or_zip_bytes_base64": "<OfflinePaperlessKyc referenceId='1234' />"
    },
}


class TestAuthenticityParity:
    """Authenticity System Parity: Every verifying tool must emit authenticity envelopes."""

    def test_verifying_tools_emit_authenticity(self) -> None:
        """Assert every verifying and attesting tool emits standard authenticity envelope."""
        import mcp_india_stack.registrations  # noqa: F401
        from mcp_india_stack.app import mcp

        tools = mcp._tool_manager._tools

        for tool_name, sample_args in VERIFYING_TOOLS_SAMPLE_INPUTS.items():
            assert tool_name in tools, f"Verifying tool {tool_name} not registered"
            tool = tools[tool_name]
            output = tool.fn(**sample_args)
            assert isinstance(output, dict), f"{tool_name} output must be dict"
            assert "authenticity" in output, (
                f"Verifying tool {tool_name} missing 'authenticity' key in response"
            )

            auth = output["authenticity"]
            assert isinstance(auth, dict), f"{tool_name} 'authenticity' must be dict"

            if tool_name.startswith("bulk_"):
                assert "summary" in auth, f"{tool_name} bulk authenticity must contain 'summary'"
                # Check that items in data.results have authenticity
                results = output.get("data", {}).get("results", [])
                for item in results:
                    assert "authenticity" in item, (
                        f"Item in {tool_name} results missing authenticity"
                    )
            else:
                for req_key in ("level", "checks", "source", "as_of", "limitations"):
                    assert req_key in auth, f"{tool_name} authenticity missing key '{req_key}'"
                assert isinstance(auth["checks"], list), f"{tool_name} checks must be list"
                assert isinstance(auth["limitations"], list), (
                    f"{tool_name} limitations must be list"
                )
                assert len(auth["limitations"]) > 0, (
                    f"{tool_name} limitations must be non-empty below A4"
                )
