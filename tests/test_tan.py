"""Tests for TAN (Tax Deduction Account Number) validator."""

from mcp_india_stack.tools.tan import validate_tan


def test_tan_valid_standard():
    result = validate_tan("PNEA12345B")
    assert result["valid"] is True
    assert result["ao_code"] == "PNE"
    assert result["entity_initial"] == "A"
    assert result["serial"] == "12345"
    assert result["check_char"] == "B"


def test_tan_lowercase_accepted():
    result = validate_tan("pnea12345b")
    assert result["valid"] is True


def test_tan_with_spaces_stripped():
    result = validate_tan("  PNEA12345B  ")
    assert result["valid"] is True


def test_tan_wrong_length_short():
    result = validate_tan("PNEA1234B")
    assert result["valid"] is False
    assert "error" in result


def test_tan_wrong_length_long():
    result = validate_tan("PNEA12345BC")
    assert result["valid"] is False


def test_tan_digit_in_first_four():
    result = validate_tan("P1EA12345B")
    assert result["valid"] is False


def test_tan_letter_in_serial_positions():
    result = validate_tan("PNEA1234AB")
    assert result["valid"] is False


def test_tan_digit_as_check_char():
    result = validate_tan("PNEA123451")
    assert result["valid"] is False


def test_tan_empty_string():
    result = validate_tan("")
    assert result["valid"] is False


def test_tan_note_in_response():
    result = validate_tan("PNEA12345B")
    assert result["valid"] is True
    full = str(result)
    assert "traces" in full.lower() or "active" in full.lower() or "verify" in full.lower()
