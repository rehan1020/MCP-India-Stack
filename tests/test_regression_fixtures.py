import json
from pathlib import Path

from mcp_india_stack.tools.gstin import validate_gstin
from mcp_india_stack.tools.ifsc import lookup_ifsc
from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.upi import validate_upi_vpa

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict[str, object]]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_regression_gstin_fixtures() -> None:
    for case in _load("gstin_cases.json"):
        result = validate_gstin(str(case["input"]))
        assert result["valid"] is case["expected_valid"]


def test_regression_pan_fixtures() -> None:
    for case in _load("pan_cases.json"):
        result = validate_pan(str(case["input"]))
        assert result["valid"] is case["expected_valid"]


def test_regression_upi_fixtures() -> None:
    for case in _load("upi_cases.json"):
        result = validate_upi_vpa(str(case["input"]))
        assert result["valid"] is case["expected_valid"]


def test_regression_ifsc_fixtures() -> None:
    for case in _load("ifsc_cases.json"):
        result = lookup_ifsc(str(case["input"]))
        assert result["found"] is case["expected_found"]
