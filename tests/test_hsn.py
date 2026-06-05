from mcp_india_stack.tools.hsn import lookup_hsn_code


def test_lookup_hsn_exact() -> None:
    result = lookup_hsn_code(code="0901")
    assert result["success"] is True
    assert "found" in result["data"]


def test_lookup_hsn_keyword() -> None:
    result = lookup_hsn_code(keyword="coffee")
    assert "found" in result["data"]


def test_hsn_single_digit_code_invalid() -> None:
    """1-digit code fails CODE_RE (min 2 digits) -> line 28 error."""
    result = lookup_hsn_code(code="9")
    assert result["success"] is False
    assert any("2-8" in e or "digit" in e.lower() for e in result["errors"])


def test_hsn_code_with_letters_invalid() -> None:
    """Code containing letters fails CODE_RE -> line 28 error."""
    result = lookup_hsn_code(code="AB12")
    assert result["success"] is False
    assert any("digit" in e.lower() for e in result["errors"])


def test_hsn_code_nine_digits_invalid() -> None:
    """9-digit code exceeds CODE_RE max of 8 -> line 28 error."""
    result = lookup_hsn_code(code="123456789")
    assert result["success"] is False
    assert any("2-8" in e or "digit" in e.lower() for e in result["errors"])


def test_hsn_code_valid_format_not_in_dataset() -> None:
    """8-digit all-nines: passes CODE_RE but not in bundled dataset -> line 37."""
    result = lookup_hsn_code(code="99999999")
    assert result["success"] is False
    assert any("not found" in e.lower() for e in result["errors"])


def test_hsn_keyword_whitespace_only() -> None:
    """Whitespace-only keyword -> stripped to '' -> line 66 error."""
    result = lookup_hsn_code(keyword="   ")
    assert result["success"] is False
    assert any("empty" in e.lower() for e in result["errors"])


def test_hsn_keyword_empty_string() -> None:
    """Empty string keyword falls to line 100."""
    result = lookup_hsn_code(code=None, keyword="")
    assert result["success"] is False


def test_hsn_no_arguments() -> None:
    """No arguments at all -> line 100: 'Provide either code or keyword'."""
    result = lookup_hsn_code()
    assert result["success"] is False
    assert any("code" in e.lower() or "keyword" in e.lower() for e in result["errors"])


def test_hsn_both_none() -> None:
    """Both code=None and keyword=None -> line 100."""
    result = lookup_hsn_code(code=None, keyword=None)
    assert result["success"] is False
    assert any("code" in e.lower() or "keyword" in e.lower() for e in result["errors"])


# --- Bug fix verification tests ---


def test_hsn_8517_rate_is_18():
    """HSN 8517 (smartphones) should be 18% IGST."""
    result = lookup_hsn_code(code="8517")
    assert result["success"] is True
    assert result["data"]["igst_rate"] == 18.0
    assert result["data"]["cgst_rate"] == 9.0


def test_hsn_9401_rate_is_18():
    """HSN 9401 (seats) should be 18% IGST."""
    result = lookup_hsn_code(code="9401")
    assert result["success"] is True
    assert result["data"]["igst_rate"] == 18.0


def test_hsn_2523_cement_rate_is_28():
    """HSN 2523 (cement) should be 28% IGST."""
    result = lookup_hsn_code(code="2523")
    assert result["success"] is True
    assert result["data"]["igst_rate"] == 28.0
