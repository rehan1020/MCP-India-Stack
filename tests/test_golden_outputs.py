"""Golden output tests for Update 5b.

Verifies that all 9 extracted tools produce bit-for-bit identical output across
6 inputs each, and that FastMCP tool manifests (names, descriptions, schemas,
annotations) remain 100% stable before and after extraction.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import mcp_india_stack.registrations  # noqa: F401
from mcp_india_stack.app import mcp
from tests.constants import (
    EXPECTED_TOOL_COUNT_ELEVATED_OFF,
    EXPECTED_TOOL_COUNT_ELEVATED_ON,
)

GOLDEN_DIR = Path(__file__).parent / "golden"


def test_tool_manifest_stability() -> None:
    """Assert FastMCP tool manifests match saved golden manifest exactly."""
    manifest_file = GOLDEN_DIR / "tool_manifest.json"
    assert manifest_file.exists(), "tool_manifest.json must exist"

    golden_manifest: dict[str, Any] = json.loads(manifest_file.read_text(encoding="utf-8"))
    current_tools = mcp._tool_manager._tools

    assert len(current_tools) in (
        EXPECTED_TOOL_COUNT_ELEVATED_OFF,
        EXPECTED_TOOL_COUNT_ELEVATED_ON,
    )
    assert set(current_tools.keys()) <= set(golden_manifest.keys())

    for name, tool in current_tools.items():
        golden = golden_manifest[name]
        assert tool.name == golden["name"]
        assert (
            inspect.cleandoc(tool.description or "").strip()
            == inspect.cleandoc(golden["description"] or "").strip()
        )
        assert tool.parameters == golden["parameters"]
        if golden["annotations"]:
            assert tool.annotations is not None
            assert getattr(tool.annotations, "readOnlyHint", None) == golden["annotations"].get(
                "readOnlyHint"
            )
            assert getattr(tool.annotations, "idempotentHint", None) == golden["annotations"].get(
                "idempotentHint"
            )
            assert getattr(tool.annotations, "openWorldHint", None) == golden["annotations"].get(
                "openWorldHint"
            )


@pytest.mark.parametrize(
    "tool_name",
    [
        "bulk_validate_gstin",
        "bulk_validate_pan",
        "bulk_validate_ifsc",
        "decode_digilocker_uri",
        "decode_pan_type",
        "lookup_bank",
        "validate_aa_consent_artifact",
        "validate_epf_code",
        "validate_esic_code",
    ],
)
def test_golden_outputs_match(tool_name: str) -> None:
    """Assert tool execution on 6 golden inputs matches golden outputs exactly."""
    golden_file = GOLDEN_DIR / "golden_outputs.json"
    assert golden_file.exists(), "golden_outputs.json must exist"

    golden_data: dict[str, list[dict[str, Any]]] = json.loads(
        golden_file.read_text(encoding="utf-8")
    )
    assert tool_name in golden_data, f"Tool {tool_name} missing from golden_outputs.json"

    cases = golden_data[tool_name]
    assert len(cases) == 6, f"Tool {tool_name} must have exactly 6 golden test cases"

    tool = mcp._tool_manager._tools[tool_name]
    for idx, case in enumerate(cases):
        inp = case["input"]
        expected = case["expected"]
        actual = tool.fn(**inp)
        assert actual == expected, (
            f"Output mismatch for {tool_name} case {idx}: actual={actual} != expected={expected}"
        )
