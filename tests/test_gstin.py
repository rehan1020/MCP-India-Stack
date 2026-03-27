from mcp_india_stack.tools.gstin import compute_gstin_checksum, validate_gstin


def test_validate_gstin_success() -> None:
    value = "27AAPFU0939F1ZV"
    result = validate_gstin(value)
    assert result["valid"] is True
    assert result["state_code"] == "27"


def test_validate_gstin_checksum_invalid() -> None:
    value = "27AAPFU0939F1ZA"
    result = validate_gstin(value)
    assert result["valid"] is False
    assert "Checksum character is invalid" in result["errors"]


def test_compute_checksum_known_vector() -> None:
    assert compute_gstin_checksum("27AAPFU0939F1Z") == "V"


def test_validate_gstin_composite_category() -> None:
    base = "99ABCDE1234F1Z"
    value = f"{base}{compute_gstin_checksum(base)}"
    result = validate_gstin(value)
    assert result["category"] == "composite_taxpayer"
    assert result["format_validity"] == "limited"


def test_validate_gstin_government_category() -> None:
    base = "27GOVDE1234F1Z"
    value = f"{base}{compute_gstin_checksum(base)}"
    result = validate_gstin(value)
    assert result["category"] == "government_department"
    assert result["format_validity"] == "limited"


def test_validate_gstin_unknown_special_category() -> None:
    base = "27A1A1A1A1A11Z"
    value = f"{base}{compute_gstin_checksum(base)}"
    result = validate_gstin(value)
    assert result["category"] == "unknown_special"
    assert result["format_validity"] == "limited"
