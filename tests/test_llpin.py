"""Tests for LLPIN (LLP Identification Number) validator."""

from mcp_india_stack.tools.llpin import validate_llpin


def test_llpin_valid_with_hyphen():
    result = validate_llpin("AAA-1234")
    assert result["valid"] is True
    assert result["prefix"] == "AAA"
    assert result["serial"] == "1234"


def test_llpin_lowercase_normalized():
    result = validate_llpin("aaa-1234")
    assert result["valid"] is True


def test_llpin_digits_in_prefix():
    result = validate_llpin("AA1-1234")
    assert result["valid"] is False


def test_llpin_letters_in_serial():
    result = validate_llpin("AAA-12AB")
    assert result["valid"] is False


def test_llpin_empty():
    result = validate_llpin("")
    assert result["valid"] is False


def test_llpin_too_long():
    result = validate_llpin("AAAA-12345")
    assert result["valid"] is False


def test_llpin_missing_hyphen():
    result = validate_llpin("AAA1234")
    assert "valid" in result


def test_llpin_mca_note_present():
    result = validate_llpin("AAA-1234")
    assert result["valid"] is True
    assert "mca" in str(result).lower() or "portal" in str(result).lower()
