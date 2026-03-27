from mcp_india_stack.tools.upi import validate_upi_vpa


def test_validate_upi_known_handle() -> None:
    result = validate_upi_vpa("user@okaxis")
    assert result["valid"] is True
    assert result["known_provider"] is True


def test_validate_upi_invalid_value() -> None:
    result = validate_upi_vpa("not-a-vpa")
    assert result["valid"] is False
