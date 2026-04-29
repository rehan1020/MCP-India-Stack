from mcp_india_stack.tools.state_code import decode_state_code


def test_decode_state_code_known() -> None:
    result = decode_state_code("27")
    assert result["found"] is True
    assert result["state_name"] == "Maharashtra"


def test_decode_state_code_unknown() -> None:
    result = decode_state_code("99")
    assert result["found"] is False


def test_decode_state_code_numeric_unknown() -> None:
    result = decode_state_code("99")
    assert result["found"] is False
    assert "error" in result


def test_decode_state_code_empty() -> None:
    result = decode_state_code("")
    assert result["found"] is False
    assert "error" in result


def test_decode_state_code_none_input() -> None:
    result = decode_state_code(None)
    assert result["found"] is False
    assert "error" in result
