from mcp_india_stack.server import (
    decode_state_code,
    lookup_hsn_code,
    lookup_ifsc,
    lookup_pincode,
    validate_gstin,
    validate_pan,
    validate_upi_vpa,
)


def test_server_tool_wrappers_return_standard_shape() -> None:
    responses = [
        validate_gstin("27AAPFU0939F1ZV"),
        validate_pan("AAAPL1234C"),
        validate_upi_vpa("user@okaxis"),
        lookup_ifsc("HDFC0000001"),
        lookup_pincode("110001"),
        lookup_hsn_code(code="0901"),
        decode_state_code("27"),
    ]
    for response in responses:
        assert "success" in response
        assert "data" in response
        assert "errors" in response
        assert "warnings" in response
        assert "source" in response
        assert "tool_version" in response
