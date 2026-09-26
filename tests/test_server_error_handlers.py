from pytest import MonkeyPatch

from mcp_india_stack import server
from mcp_india_stack.registrations import banking, finance, kyc, legal, lookup, tax


def _assert_structured_error(response: dict[str, object], fragment: str) -> None:
    assert response["success"] is False
    errors = response.get("errors", [])
    assert isinstance(errors, list)
    assert any(fragment in str(item) for item in errors)


def test_lookup_ifsc_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.banking.core_lookup_ifsc",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-ifsc")),
    )
    response = banking.lookup_ifsc("HDFC0000001")
    _assert_structured_error(response, "IFSC lookup failed")


def test_validate_gstin_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_gstin",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-gstin")),
    )
    response = kyc.validate_gstin("27AAPFU0939F1ZV")
    _assert_structured_error(response, "GSTIN validation failed")


def test_validate_pan_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_pan",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-pan")),
    )
    response = kyc.validate_pan("AAAPL1234C")
    _assert_structured_error(response, "PAN validation failed")


def test_validate_upi_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_upi_vpa",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-upi")),
    )
    response = kyc.validate_upi_vpa("user@okaxis")
    _assert_structured_error(response, "UPI validation failed")


def test_lookup_pincode_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.lookup.core_lookup_pincode",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-pincode")),
    )
    response = lookup.lookup_pincode("110001")
    _assert_structured_error(response, "Pincode lookup failed")


def test_lookup_hsn_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.lookup.core_lookup_hsn_code",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-hsn")),
    )
    response = lookup.lookup_hsn_code(code="0901")
    _assert_structured_error(response, "HSN lookup failed")


def test_decode_state_code_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.lookup.core_decode_state_code",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-state")),
    )
    response = lookup.decode_state_code("27")
    _assert_structured_error(response, "State code decode failed")


def test_validate_aadhaar_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_aadhaar",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-aadhaar")),
    )
    response = kyc.validate_aadhaar("295945837261")
    _assert_structured_error(response, "Aadhaar validation failed")


def test_validate_voter_id_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.tools.voter_id.validate_voter_id",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-voter")),
    )
    response = kyc.validate_voter_id("ABC1234567")
    _assert_structured_error(response, "Voter ID validation failed")


def test_validate_driving_license_wrapper_handles_unexpected_error(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_driving_license",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-dl")),
    )
    response = kyc.validate_driving_license("MH0220191234567")
    _assert_structured_error(response, "DL validation failed")


def test_validate_passport_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.tools.passport.validate_passport",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-passport")),
    )
    response = kyc.validate_passport("A1234567")
    _assert_structured_error(response, "Passport validation failed")


def test_validate_cin_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.kyc.core_validate_cin",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-cin")),
    )
    response = kyc.validate_cin("L17110MH1973PLC019786")
    _assert_structured_error(response, "CIN validation failed")


def test_validate_din_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.tools.din.validate_din",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom-din")),
    )
    response = kyc.validate_din("00012345")
    _assert_structured_error(response, "DIN validation failed")


def test_calculate_income_tax_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.tax.core_calculate_income_tax",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-tax")),
    )
    response = tax.calculate_income_tax(1500000)
    _assert_structured_error(response, "Income tax calculation failed")


def test_calculate_tds_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.tax.core_calculate_tds",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-tds")),
    )
    response = tax.calculate_tds(
        section="194C_individual", payment_amount=100000, pan_available=True
    )
    _assert_structured_error(response, "TDS calculation failed")


def test_calculate_gst_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.tax.core_calculate_gst",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-gst")),
    )
    response = tax.calculate_gst(amount=10000, gst_rate=18, transaction_type="intra_state")
    _assert_structured_error(response, "GST calculation failed")


def test_calculate_surcharge_wrapper_handles_unexpected_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.tax.core_calculate_surcharge",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-surcharge")),
    )
    response = tax.calculate_surcharge(total_income=60000000, base_tax=15000000, regime="new")
    _assert_structured_error(response, "Surcharge calculation failed")


def test_server_main_runs_stdio_transport(monkeypatch: MonkeyPatch) -> None:
    called: list[str] = []

    def fake_run(*, transport: str) -> None:
        called.append(transport)

    monkeypatch.setattr(server.mcp, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["mcp-india-stack"])
    server.main()
    assert called == ["stdio"]


def test_calculate_epf_esic_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.banking.core_calculate_epf_esic",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-epf")),
    )
    response = banking.calculate_epf_esic(basic_wages=25000, gross_wages=40000)
    assert response["success"] is False


def test_calculate_emi_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.finance.core_calculate_emi",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-emi")),
    )
    response = finance.calculate_emi(principal=1000000, annual_interest_rate=8.5, tenure_months=120)
    assert response["success"] is False


def test_calculate_gratuity_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.finance.core_calculate_gratuity",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-gratuity")),
    )
    response = finance.calculate_gratuity(last_drawn_salary=50000, years_of_service=7)
    assert response["success"] is False


def test_calculate_ppf_maturity_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.finance.core_calculate_ppf_maturity",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-ppf")),
    )
    response = finance.calculate_ppf_maturity(annual_investment=150000)
    assert response["success"] is False


def test_get_regulatory_deadlines_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.legal.core_get_regulatory_deadlines",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-calendar")),
    )
    response = legal.get_regulatory_deadlines(category="GST")
    assert response["success"] is False


def test_calculate_salary_restructuring_wrapper_handles_error(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_india_stack.registrations.tax.core_calculate_salary_restructuring",
        lambda **_: (_ for _ in ()).throw(RuntimeError("boom-salary")),
    )
    response = tax.calculate_salary_restructuring(current_gross=1800000, current_basic_ratio=0.5)
    assert response["success"] is False
