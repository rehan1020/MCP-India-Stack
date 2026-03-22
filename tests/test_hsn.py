from mcp_india_stack.tools.hsn import lookup_hsn_code


def test_lookup_hsn_exact() -> None:
    result = lookup_hsn_code(code="0901")
    assert "found" in result


def test_lookup_hsn_keyword() -> None:
    result = lookup_hsn_code(keyword="coffee")
    assert "found" in result
