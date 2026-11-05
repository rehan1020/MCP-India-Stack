"""Backward compatibility tests for the Authenticity System (PR 8a).

Verifies that excluding the additive 'authenticity' and 'authenticity_summary'
fields, tool outputs match pre-authenticity golden outputs bit-for-bit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import mcp_india_stack.registrations  # noqa: F401
from mcp_india_stack.app import mcp

GOLDEN_DIR = Path(__file__).parent / "golden"


def _strip_authenticity(obj: Any) -> Any:
    """Recursively strip additive authenticity fields from tool outputs."""
    if isinstance(obj, dict):
        return {
            k: _strip_authenticity(v)
            for k, v in obj.items()
            if k not in ("authenticity", "authenticity_summary")
        }
    if isinstance(obj, list):
        return [_strip_authenticity(item) for item in obj]
    return obj


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
def test_golden_backward_compatibility(tool_name: str) -> None:
    """Assert actual outputs without authenticity fields match pre-update golden data."""
    pre_golden_file = GOLDEN_DIR / "golden_outputs_pre_authenticity.json"
    assert pre_golden_file.exists(), (
        "golden_outputs_pre_authenticity.json must exist for backward compat test"
    )

    pre_golden_data: dict[str, list[dict[str, Any]]] = json.loads(
        pre_golden_file.read_text(encoding="utf-8")
    )
    assert tool_name in pre_golden_data, f"Tool {tool_name} missing from pre-update golden data"

    cases = pre_golden_data[tool_name]
    tool = mcp._tool_manager._tools[tool_name]

    for idx, case in enumerate(cases):
        inp = case["input"]
        expected_pre = case["expected"]
        actual = tool.fn(**inp)
        actual_stripped = _strip_authenticity(actual)
        expected_stripped = _strip_authenticity(expected_pre)
        assert actual_stripped == expected_stripped, (
            f"Backward compatibility mismatch for {tool_name} case {idx}:\n"
            f"actual_stripped={actual_stripped}\n"
            f"expected_pre={expected_stripped}"
        )
