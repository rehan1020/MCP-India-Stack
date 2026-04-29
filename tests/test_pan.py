from mcp_india_stack.server import decode_pan_type
from mcp_india_stack.tools.pan import validate_pan


def test_validate_pan_success() -> None:
    result = validate_pan("AAAPL1234C")
    assert result["valid"] is True
    assert result["entity_type"] == "Individual"


def test_validate_pan_invalid_length() -> None:
    result = validate_pan("AAA1")
    assert result["valid"] is False


def test_decode_pan_type_firm() -> None:
    result = decode_pan_type("AAPFU0939F")
    assert result["success"] is True
    assert result["data"]["entity_type_label"] == "Firm"
    assert result["data"]["entity_type_code"] == "F"


def test_decode_pan_type_llp() -> None:
    result = decode_pan_type("AAAEU1234A")
    assert result["success"] is True
    assert result["data"]["entity_type_label"] == "Limited Liability Partnership (LLP)"


def test_decode_pan_type_trust() -> None:
    result = decode_pan_type("AAATU1234A")
    assert result["success"] is True
    assert result["data"]["entity_type_label"] == "Trust"


def test_validate_pan_and_decode_pan_type_agree() -> None:
    pan = "AAPFU0939F"
    validate_result = validate_pan(pan)
    decode_result = decode_pan_type(pan)
    assert validate_result["entity_type"] == decode_result["data"]["entity_type_label"]
