from mcp_india_stack.tools.pincode import lookup_pincode


def test_lookup_pincode_invalid() -> None:
    result = lookup_pincode("abc")
    assert result["found"] is False


def test_lookup_pincode_known() -> None:
    result = lookup_pincode("110001")
    assert "found" in result
