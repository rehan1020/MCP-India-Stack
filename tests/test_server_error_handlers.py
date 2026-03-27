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


# --- v0.2.0 error handler tests ---


def test_validate_aadhaar_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_aadhaar",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-aadhaar")),
    )
    response = server.validate_aadhaar("295945837261")
    _assert_structured_error(response, "Aadhaar validation failed")


def test_validate_voter_id_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_voter_id",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-voter")),
    )
    response = server.validate_voter_id("ABC1234567")
    _assert_structured_error(response, "Voter ID validation failed")


def test_validate_driving_license_wrapper_handles_unexpected_error(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_driving_license",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-dl")),
    )
    response = server.validate_driving_license("MH0220191234567")
    _assert_structured_error(response, "DL validation failed")


def test_validate_passport_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_passport",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-passport")),
    )
    response = server.validate_passport("A1234567")
    _assert_structured_error(response, "Passport validation failed")


def test_validate_cin_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_cin",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-cin")),
    )
    response = server.validate_cin("L17110MH1973PLC019786")
    _assert_structured_error(response, "CIN validation failed")


def test_validate_din_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_validate_din",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-din")),
    )
    response = server.validate_din("00012345")
    _assert_structured_error(response, "DIN validation failed")


def test_calculate_income_tax_wrapper_handles_unexpected_error(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_calculate_income_tax",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-tax")),
    )
    response = server.calculate_income_tax(1_500_000)
    _assert_structured_error(response, "Income tax calculation failed")


def test_calculate_tds_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_calculate_tds",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-tds")),
    )
    response = server.calculate_tds(
        section="194C_individual", payment_amount=100_000, pan_available=True
    )
    _assert_structured_error(response, "TDS calculation failed")


def test_calculate_gst_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_calculate_gst",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-gst")),
    )
    response = server.calculate_gst(amount=10_000, gst_rate=18, transaction_type="intra_state")
    _assert_structured_error(response, "GST calculation failed")


def test_calculate_surcharge_wrapper_handles_unexpected_error(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.server.core_calculate_surcharge",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-surcharge")),
    )
    response = server.calculate_surcharge(
        total_income=60_000_000, base_tax=15_000_000, regime="new"
    )
    _assert_structured_error(response, "Surcharge calculation failed")


def test_server_main_runs_stdio_transport(monkeypatch: MonkeyPatch) -> None:
    called: list[str] = []

    def fake_run(*, transport: str) -> None:
        called.append(transport)

    monkeypatch.setattr(server.mcp, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["mcp-india-stack"])
    server.main()
    assert called == ["stdio"]
