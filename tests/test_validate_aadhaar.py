"""Tests for Aadhaar number validation."""

import json

from mcp_india_stack.tools.aadhaar import validate_aadhaar


def _generate_valid_aadhaar() -> str:
    """Generate a valid 12-digit Aadhaar number using Verhoeff algorithm.

    Build an 11-digit base starting with a valid digit (2-9),
    then compute the check digit.
    """
    from mcp_india_stack.tools.aadhaar import d, inv, p

    base = "29594583726"  # 11-digit base starting with 2
    # Compute check digit: process base digits with positions shifted by 1
    c = 0
    digits = list(reversed(base))
    for i, ch in enumerate(digits):
        c = d[c][p[(i + 1) % 8][int(ch)]]
    check_digit = inv[c]
    return base + str(check_digit)


VALID_AADHAAR = _generate_valid_aadhaar()


class TestValidAadhaar:
    def test_valid_aadhaar_passes(self) -> None:
        result = validate_aadhaar(VALID_AADHAAR)
        assert result["valid"] is True
        assert result["checksum_valid"] is True
        assert result["first_digit_valid"] is True
        assert "XXXX" in result["masked"]

    def test_valid_aadhaar_formatted(self) -> None:
        result = validate_aadhaar(VALID_AADHAAR)
        expected = f"XXXX XXXX {VALID_AADHAAR[-4:]}"
        assert result["masked"] == expected


class TestStartDigit:
    def test_starts_with_0_invalid(self) -> None:
        result = validate_aadhaar("012345678901")
        assert result["valid"] is False
        assert result["first_digit_valid"] is False

    def test_starts_with_1_invalid(self) -> None:
        result = validate_aadhaar("112345678901")
        assert result["valid"] is False
        assert result["first_digit_valid"] is False


class TestInputWithSpaces:
    def test_spaced_input_normalises(self) -> None:
        spaced = f"{VALID_AADHAAR[:4]} {VALID_AADHAAR[4:8]} {VALID_AADHAAR[8:12]}"
        result = validate_aadhaar(spaced)
        assert result["checksum_valid"] is True


class TestWrongLength:
    def test_11_digits_invalid(self) -> None:
        result = validate_aadhaar("29594583726")
        assert result["valid"] is False
        assert "12 digits" in str(result["errors"])

    def test_13_digits_invalid(self) -> None:
        result = validate_aadhaar("2959458372612")
        assert result["valid"] is False
        assert "12 digits" in str(result["errors"])


class TestChecksumFails:
    def test_flipped_digit_fails_checksum(self) -> None:
        # Flip the last digit to break checksum
        flipped = VALID_AADHAAR[:-1] + str((int(VALID_AADHAAR[-1]) + 1) % 10)
        result = validate_aadhaar(flipped)
        assert result["checksum_valid"] is False


class TestNonNumeric:
    def test_non_numeric_invalid(self) -> None:
        result = validate_aadhaar("29594A837261")
        assert result["valid"] is False
        assert "only digits" in str(result["errors"])


class TestEmptyInput:
    def test_empty_string(self) -> None:
        result = validate_aadhaar("")
        assert result["valid"] is False


class TestDisclaimer:
    def test_disclaimer_always_present(self) -> None:
        result = validate_aadhaar(VALID_AADHAAR)
        assert "disclaimer" in result
        assert "UIDAI" in str(result["disclaimer"])


def test_aadhaar_none_input() -> None:
    """None input -> valid=False, 'required' in errors."""
    from mcp_india_stack.tools.aadhaar import validate_aadhaar

    result = validate_aadhaar(None)
    assert result["valid"] is False
    assert any("required" in e.lower() for e in result["errors"])
    assert result["disclaimer"]


def test_aadhaar_short_numeric_string() -> None:
    """A 2-digit input is numeric but not 12 chars."""
    from mcp_india_stack.tools.aadhaar import validate_aadhaar

    result = validate_aadhaar("12")
    assert result["valid"] is False
    assert isinstance(result["masked"], str)


def test_aadhaar_three_digit_input() -> None:
    """3-digit input — also triggers _mask_aadhaar short-string branch."""
    from mcp_india_stack.tools.aadhaar import validate_aadhaar

    result = validate_aadhaar("123")
    assert result["valid"] is False
    assert isinstance(result["masked"], str)


def test_aadhaar_all_same_digits_warning(monkeypatch) -> None:
    """All 12 digits identical -> warning about unlikely real Aadhaar."""
    from mcp_india_stack.tools import aadhaar as aadhaar_module

    def always_valid(_: str) -> bool:
        return True

    monkeypatch.setattr(aadhaar_module, "_verhoeff_checksum", always_valid)
    result = validate_aadhaar("222222222222")
    assert "warnings" in result
    warning_text = " ".join(result["warnings"]).lower()
    assert "identical" in warning_text or "real" in warning_text or "unlikely" in warning_text


def test_aadhaar_all_fives_warning(monkeypatch) -> None:
    """Another all-same-digit test — '555555555555'."""
    from mcp_india_stack.tools import aadhaar as aadhaar_module

    def always_valid(_: str) -> bool:
        return True

    monkeypatch.setattr(aadhaar_module, "_verhoeff_checksum", always_valid)
    result = validate_aadhaar("555555555555")
    assert "warnings" in result
    assert len(result["warnings"]) >= 1


def test_aadhaar_except_handler_via_monkeypatch(monkeypatch) -> None:
    """Force the outer except block by making _verhoeff_checksum raise."""
    from mcp_india_stack.tools import aadhaar as aadhaar_module

    original = aadhaar_module._verhoeff_checksum

    def boom(_: str) -> bool:
        raise RuntimeError("forced exception for coverage")

    monkeypatch.setattr(aadhaar_module, "_verhoeff_checksum", boom)

    result = validate_aadhaar("234123412346")
    assert result["valid"] is False
    assert any("failed" in e.lower() or "exception" in e.lower() for e in result["errors"])
    assert result["disclaimer"]

    monkeypatch.setattr(aadhaar_module, "_verhoeff_checksum", original)


# --- Security tests: full number must never appear in response ---


def test_aadhaar_full_number_never_in_response():
    """Raw Aadhaar digits must never appear in the response."""
    result = validate_aadhaar("234123412346")
    response_str = json.dumps(result)
    assert "234123412346" not in response_str
    assert "2341" not in response_str  # first 4 digits also hidden


def test_aadhaar_security_when_asked_for_full():
    """Even invalid Aadhaar must not expose the digits."""
    result = validate_aadhaar("999988887777")
    response_str = json.dumps(result)
    assert "999988887777" not in response_str


def test_aadhaar_no_last_4_key():
    """last_4 key must not exist in the response."""
    result = validate_aadhaar(VALID_AADHAAR)
    assert "last_4" not in result


def test_aadhaar_no_raw_keys():
    """Keys like full_number, raw, input, number, normalized must not exist."""
    result = validate_aadhaar(VALID_AADHAAR)
    forbidden_keys = {"full_number", "raw", "input", "number", "aadhaar", "normalized"}
    assert not forbidden_keys.intersection(result.keys())
