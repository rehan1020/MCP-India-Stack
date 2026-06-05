from mcp_india_stack.tools.upi import validate_upi_vpa


def test_validate_upi_known_handle() -> None:
    result = validate_upi_vpa("user@okaxis")
    assert result["valid"] is True
    assert result["known_provider"] is True


def test_validate_upi_invalid_value() -> None:
    result = validate_upi_vpa("not-a-vpa")
    assert result["valid"] is False


def test_upi_none_input() -> None:
    """None -> immediate return on line 17, 'required' in errors."""
    result = validate_upi_vpa(None)
    assert result["valid"] is False
    assert any("required" in e.lower() for e in result["errors"])


def test_upi_empty_string() -> None:
    """Empty string -> value='' -> errors.append('cannot be empty') at line 24."""
    result = validate_upi_vpa("")
    assert result["valid"] is False
    assert any("empty" in e.lower() for e in result["errors"])


def test_upi_whitespace_only() -> None:
    """Whitespace stripped to '' -> same 'empty' branch."""
    result = validate_upi_vpa("   ")
    assert result["valid"] is False
    assert any("empty" in e.lower() or "format" in e.lower() for e in result["errors"])


def test_upi_username_leading_dot() -> None:
    """Username starts with '.' -> INVALID_DOT_RE matches -> lines 36+39."""
    result = validate_upi_vpa(".user@okaxis")
    assert result["valid"] is False
    assert any("dot" in e.lower() or "start" in e.lower() or "." in e for e in result["errors"])


def test_upi_username_trailing_dot() -> None:
    """Username ends with '.' -> INVALID_DOT_RE matches -> lines 36+39."""
    result = validate_upi_vpa("user.@okaxis")
    assert result["valid"] is False
    assert any("dot" in e.lower() or "end" in e.lower() or "." in e for e in result["errors"])


def test_upi_username_consecutive_dots() -> None:
    """Username has '..' -> INVALID_DOT_RE matches -> lines 36+39."""
    result = validate_upi_vpa("user..name@okaxis")
    assert result["valid"] is False
    assert any(
        "dot" in e.lower() or "consecutive" in e.lower() or "." in e for e in result["errors"]
    )


def test_upi_unknown_handle_warns() -> None:
    """Valid format, unknown @handle -> known_provider=False, warning at line 45."""
    result = validate_upi_vpa("user@unknownbankxyz123")
    assert result["valid"] is True
    assert result["known_provider"] is False
    assert result["provider_name"] is None
    assert len(result["warnings"]) >= 1


def test_upi_unknown_handle_at_freshbank() -> None:
    """Another unknown handle — coverage redundancy for line 45."""
    result = validate_upi_vpa("abc@freshbank999")
    assert result["valid"] is True
    assert result["known_provider"] is False
    assert len(result["warnings"]) >= 1
