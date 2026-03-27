from mcp_india_stack.tools.pan import validate_pan


def test_validate_pan_success() -> None:
    result = validate_pan("AAAPL1234C")
    assert result["valid"] is True
    assert result["entity_type"] == "Individual"


def test_validate_pan_invalid_length() -> None:
    result = validate_pan("AAA1")
    assert result["valid"] is False
