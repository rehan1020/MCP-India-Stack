from pytest import MonkeyPatch

from mcp_india_stack import server


def _assert_structured_error(response: dict[str, object], fragment: str) -> None:
    assert response["success"] is False
    errors = response.get("errors", [])
    assert isinstance(errors, list)
    assert any(fragment in str(item) for item in errors)


def test_lookup_ifsc_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_lookup_ifsc",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-ifsc")),
    )
    response = server.lookup_ifsc("HDFC0000001")
    _assert_structured_error(response, "IFSC lookup failed")


def test_validate_gstin_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_gstin",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-gstin")),
    )
    response = server.validate_gstin("27AAPFU0939F1ZV")
    _assert_structured_error(response, "GSTIN validation failed")


def test_validate_pan_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_pan",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-pan")),
    )
    response = server.validate_pan("AAAPL1234C")
    _assert_structured_error(response, "PAN validation failed")


def test_validate_upi_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_upi_vpa",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-upi")),
    )
    response = server.validate_upi_vpa("user@okaxis")
    _assert_structured_error(response, "UPI validation failed")


def test_lookup_pincode_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_lookup_pincode",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-pincode")),
    )
    response = server.lookup_pincode("110001")
    _assert_structured_error(response, "Pincode lookup failed")


def test_lookup_hsn_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_lookup_hsn_code",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-hsn")),
    )
    response = server.lookup_hsn_code(code="0901")
    _assert_structured_error(response, "HSN lookup failed")


def test_decode_state_code_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_decode_state_code",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-state")),
    )
    response = server.decode_state_code("27")
    _assert_structured_error(response, "State code decode failed")


def test_server_main_runs_stdio_transport(monkeypatch: MonkeyPatch) -> None:
    called: list[str] = []

    def fake_run(*, transport: str) -> None:
        called.append(transport)

    monkeypatch.setattr(server.mcp, "run", fake_run)
    server.main()
    assert called == ["stdio"]
