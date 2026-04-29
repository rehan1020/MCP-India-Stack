from mcp_india_stack.tools.pincode import lookup_pincode


def test_lookup_pincode_invalid() -> None:
    result = lookup_pincode("abc")
    assert result["found"] is False


def test_lookup_pincode_known() -> None:
    result = lookup_pincode("110001")
    assert "found" in result


def test_lookup_pincode_non_numeric() -> None:
    result = lookup_pincode("ABCDEF")
    assert result["found"] is False
    assert len(result.get("errors", [])) > 0


def test_lookup_pincode_5_digits() -> None:
    result = lookup_pincode("40000")
    assert result["found"] is False


def test_lookup_pincode_7_digits() -> None:
    result = lookup_pincode("4000011")
    assert result["found"] is False


def test_lookup_pincode_not_found() -> None:
    result = lookup_pincode("000000")
    assert result["found"] is False
    assert "not found" in str(result.get("errors", [])).lower()


def test_lookup_pincode_none_input() -> None:
    result = lookup_pincode(None)
    assert result["found"] is False
    assert "required" in str(result.get("errors", [])).lower()


def test_lookup_pincode_5_digits_rejected_not_padded() -> None:
    result = lookup_pincode("12345")
    assert result["valid"] is False
    assert result["confidence"] == 0.0
    assert "6 digits" in result["error_reason"].lower()
    assert "not found" not in result["error_reason"].lower()


def test_lookup_pincode_4_digits_rejected() -> None:
    result = lookup_pincode("4000")
    assert result["valid"] is False
    assert "6 digits" in result["error_reason"].lower()


def test_lookup_pincode_7_digits_rejected() -> None:
    result = lookup_pincode("4000011")
    assert result["valid"] is False
    assert "6 digits" in result["error_reason"].lower()


def test_lookup_pincode_6_digits_still_works() -> None:
    result = lookup_pincode("400001")
    assert result["valid"] is True
    assert result["normalized_input"] == "400001"
