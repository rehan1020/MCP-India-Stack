from mcp_india_stack.tools.state_code import decode_state_code


def test_decode_state_code_known() -> None:
    result = decode_state_code("27")
    assert result["success"] is True
    assert result["data"]["found"] is True
    assert result["data"]["state_name"] == "Maharashtra"


def test_decode_state_code_unknown() -> None:
    result = decode_state_code("99")
    assert result["success"] is False
    assert result["data"]["found"] is False


def test_decode_state_code_numeric_unknown() -> None:
    result = decode_state_code("99")
    assert result["success"] is False
    assert result["data"]["found"] is False
    assert len(result["errors"]) > 0


def test_decode_state_code_empty() -> None:
    result = decode_state_code("")
    assert result["success"] is False
    assert result["data"]["found"] is False
    assert len(result["errors"]) > 0


def test_decode_state_code_none_input() -> None:
    result = decode_state_code(None)
    assert result["success"] is False
    assert result["data"]["found"] is False
    assert len(result["errors"]) > 0
