"""Tests for Aadhaar number validation."""

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
        assert result["aadhaar"] == VALID_AADHAAR

    def test_valid_aadhaar_formatted(self) -> None:
        result = validate_aadhaar(VALID_AADHAAR)
        expected = f"{VALID_AADHAAR[:4]} {VALID_AADHAAR[4:8]} {VALID_AADHAAR[8:12]}"
        assert result["formatted"] == expected


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
        assert result["aadhaar"] == VALID_AADHAAR
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
