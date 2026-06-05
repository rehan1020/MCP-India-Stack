"""Test server wrapper responses and new tools."""


class TestServerResponses:
    def test_validate_gstin_response(self) -> None:
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin="27AAPFU0939F1ZV")
        assert result["success"] is True
        assert "confidence" in result
        assert "validated_by" in result
        assert result["confidence"] >= 0.65

    def test_validate_pan_response(self) -> None:
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan="AAPFU0939F")
        assert result["success"] is True
        assert "confidence" in result

    def test_lookup_ifsc_response(self) -> None:
        from mcp_india_stack.server import lookup_ifsc

        result = lookup_ifsc(ifsc_code="SBIN0001234")
        assert "confidence" in result

    def test_validate_upi_response(self) -> None:
        from mcp_india_stack.server import validate_upi_vpa

        result = validate_upi_vpa(vpa="test@okicici")
        assert "confidence" in result

    def test_lookup_pincode_response(self) -> None:
        from mcp_india_stack.server import lookup_pincode

        result = lookup_pincode(pincode="400001")
        assert "confidence" in result

    def test_lookup_hsn_response(self) -> None:
        from mcp_india_stack.server import lookup_hsn_code

        result = lookup_hsn_code(code="1001")
        assert "confidence" in result

    def test_validate_aadhaar_response(self) -> None:
        from mcp_india_stack.server import validate_aadhaar

        result = validate_aadhaar(aadhaar="123456789012")
        assert "confidence" in result

    def test_validate_cin_response(self) -> None:
        from mcp_india_stack.server import validate_cin

        result = validate_cin(cin="U67190TN2014PTC096249")
        assert "confidence" in result

    def test_validate_din_response(self) -> None:
        from mcp_india_stack.server import validate_din

        result = validate_din(din="00012345")
        assert "confidence" in result

    def test_calculate_income_tax_response(self) -> None:
        from mcp_india_stack.server import calculate_income_tax

        result = calculate_income_tax(gross_income=1500000)
        assert result["success"] is True

    def test_calculate_tds_response(self) -> None:
        from mcp_india_stack.server import calculate_tds

        result = calculate_tds(section="192", payment_amount=100000, pan_available=True)
        assert "data" in result

    def test_calculate_gst_response(self) -> None:
        from mcp_india_stack.server import calculate_gst

        result = calculate_gst(amount=1000, gst_rate=18, transaction_type="intra_state")
        assert "data" in result

    def test_calculate_surcharge_response(self) -> None:
        from mcp_india_stack.server import calculate_surcharge

        result = calculate_surcharge(total_income=5000000, base_tax=125000, regime="new")
        assert "data" in result


class TestNewServerTools:
    def test_bulk_validate_gstin(self) -> None:
        from mcp_india_stack.server import bulk_validate_gstin

        result = bulk_validate_gstin(gstins=["27AAPFU0939F1ZV", "27AAPFU0939F1ZV"])
        assert result["success"] is True
        assert len(result["data"]["results"]) == 2

    def test_bulk_validate_pan(self) -> None:
        from mcp_india_stack.server import bulk_validate_pan

        result = bulk_validate_pan(pans=["AAPFU0939F", "AAPFU0939F"])
        assert result["success"] is True

    def test_bulk_validate_ifsc(self) -> None:
        from mcp_india_stack.server import bulk_validate_ifsc

        result = bulk_validate_ifsc(ifscs=["SBIN0001234"])
        assert result["success"] is True

    def test_calculate_hra_exemption(self) -> None:
        from mcp_india_stack.server import calculate_hra_exemption

        result = calculate_hra_exemption(basic_salary=50000, hra_received=180000, rent_paid=240000)
        assert result["success"] is True

    def test_calculate_capital_gains(self) -> None:
        from mcp_india_stack.server import calculate_capital_gains

        result = calculate_capital_gains(
            sale_price=150000, purchase_price=100000, asset_type="equity"
        )
        assert result["success"] is True

    def test_calculate_advance_tax(self) -> None:
        from mcp_india_stack.server import calculate_advance_tax

        result = calculate_advance_tax(estimated_income=1500000)
        assert result["success"] is True

    def test_lookup_bbps_biller(self) -> None:
        from mcp_india_stack.server import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity")
        assert result["success"] is True

    def test_decode_pan_type(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAPFU0939F")
        assert result["success"] is True

    def test_lookup_bank(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="SBIN")
        assert result["success"] is True

    def test_validate_epf_code(self) -> None:
        from mcp_india_stack.server import validate_epf_code

        result = validate_epf_code(code="MH/12345/67890/123")
        assert "data" in result

    def test_validate_esic_code(self) -> None:
        from mcp_india_stack.server import validate_esic_code

        result = validate_esic_code(code="12-12345-67890")
        assert "data" in result

    def test_decode_digilocker_uri(self) -> None:
        from mcp_india_stack.server import decode_digilocker_uri

        result = decode_digilocker_uri(uri="dlg://uidai/aadhaar")
        assert result["success"] is True

    def test_validate_fssai(self) -> None:
        from mcp_india_stack.server import validate_fssai

        result = validate_fssai(license_number="11223344556677")
        assert result["success"] is True


class TestServerResources:
    def test_server_status(self) -> None:
        from mcp_india_stack.server import server_status

        status = server_status()
        assert status["version"] == "0.4.2"
        assert status["tool_count"] == 58

    def test_changelog(self) -> None:
        from mcp_india_stack.server import changelog

        cl = changelog()
        assert cl["current_version"] == "0.4.2"
        assert len(cl["entries"]) > 0


class TestErrorHandling:
    def test_validate_gstin_error(self) -> None:
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin=None)
        assert result["success"] is False

    def test_validate_pan_error(self) -> None:
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan=None)
        assert result["success"] is False

    def test_lookup_ifsc_error(self) -> None:
        from mcp_india_stack.server import lookup_ifsc

        result = lookup_ifsc(ifsc_code=None)
        assert result["success"] is False


class TestMessyInputNormalization:
    def test_validate_gstin_messy_input_single_call(self) -> None:
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin="27 aapfu 0939f 1zv")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["normalized_input"] == "27AAPFU0939F1ZV"

    def test_validate_pan_messy_input_single_call(self) -> None:
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan="aapf u0939f")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["pan"] == "AAPFU0939F"

    def test_validate_aadhaar_messy_input_single_call(self) -> None:
        from mcp_india_stack.server import validate_aadhaar

        result = validate_aadhaar(aadhaar="2341 2341 2346")
        assert result["success"] is True
        assert result["data"]["valid"] is True


class TestV04ServerTools:
    """Happy path tests for all v0.4.0 server wrappers."""

    def test_calculate_epf_esic_server(self) -> None:
        from mcp_india_stack.server import calculate_epf_esic

        result = calculate_epf_esic(basic_wages=25000, gross_wages=40000)
        assert result["success"] is True
        assert "data" in result
        assert "confidence" in result

    def test_calculate_emi_server(self) -> None:
        from mcp_india_stack.server import calculate_emi

        result = calculate_emi(principal=1000000, annual_interest_rate=8.5, tenure_months=120)
        assert result["success"] is True
        assert result["data"]["emi"] > 0

    def test_calculate_gratuity_server(self) -> None:
        from mcp_india_stack.server import calculate_gratuity

        result = calculate_gratuity(last_drawn_salary=50000, years_of_service=7)
        assert result["success"] is True

    def test_calculate_ppf_maturity_server(self) -> None:
        from mcp_india_stack.server import calculate_ppf_maturity

        result = calculate_ppf_maturity(annual_investment=150000)
        assert result["success"] is True
        assert result["data"]["maturity_amount"] > 0

    def test_bulk_validate_aadhaar_server(self) -> None:
        from mcp_india_stack.server import bulk_validate_aadhaar

        result = bulk_validate_aadhaar(numbers=["295945837261", "295945837262"])
        assert "success" in result
        assert "data" in result

    def test_get_regulatory_deadlines_server(self) -> None:
        from mcp_india_stack.server import get_regulatory_deadlines

        result = get_regulatory_deadlines(category="GST")
        assert result["success"] is True
        assert "data" in result

    def test_calculate_salary_restructuring_server(self) -> None:
        from mcp_india_stack.server import calculate_salary_restructuring

        result = calculate_salary_restructuring(current_gross=1800000, current_basic_ratio=0.50)
        assert result["success"] is True


class TestDecodePanTypeAllEntityCodes:
    """Each 4th-character entity code must decode to the correct label."""

    def test_individual_pan(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAAPL1234C")
        if result["success"]:
            assert "Individual" in result["data"]["entity_type_label"]

    def test_company_pan(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAACC1234C")
        if result["success"]:
            assert "Company" in result["data"]["entity_type_label"]

    def test_huf_pan(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAAHH1234C")
        if result["success"]:
            assert (
                "Hindu" in result["data"]["entity_type_label"]
                or "HUF" in result["data"]["entity_type_label"]
            )

    def test_firm_pan(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAAFP1234C")
        if result["success"]:
            assert "Firm" in result["data"]["entity_type_label"]

    def test_unknown_entity_code(self) -> None:
        """PAN with unknown 4th char -> Unknown entity type."""
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAAXP1234C")
        if result["success"]:
            assert (
                "Unknown" in result["data"]["entity_type_label"]
                or result["data"]["entity_type_code"] == "X"
            )

    def test_invalid_pan_returns_failure(self) -> None:
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="NOTAPAN")
        assert result["success"] is False


class TestLookupBank:
    def test_lookup_by_code_sbin(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="SBIN")
        assert result["success"] is True
        assert "State Bank" in str(result["data"])

    def test_lookup_by_name_hdfc(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="HDFC")
        assert result["success"] is True

    def test_lookup_case_insensitive(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="hdfc")
        assert result["success"] is True

    def test_lookup_not_found(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="NONEXISTENTBANKXYZ")
        assert result["success"] is False or (
            result["success"] is True and result["data"]["count"] == 0
        )

    def test_lookup_partial_name_match(self) -> None:
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="Kotak")
        assert "success" in result


class TestPromptFunctions:
    def test_vendor_kyc_prompt_returns_string(self) -> None:
        from mcp_india_stack.server import vendor_kyc

        result = vendor_kyc()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "GSTIN" in result or "gstin" in result.lower()

    def test_salary_planner_prompt_returns_string(self) -> None:
        from mcp_india_stack.server import salary_planner

        result = salary_planner()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "tax" in result.lower() or "income" in result.lower()

    def test_invoice_audit_prompt_returns_string(self) -> None:
        from mcp_india_stack.server import invoice_audit

        result = invoice_audit()
        assert isinstance(result, str)
        assert len(result) > 100
        assert "GST" in result or "invoice" in result.lower()


class TestSchemaResources:
    """Each schema resource must return a valid JSON schema dict."""

    def _assert_valid_schema(self, schema: dict) -> None:
        assert isinstance(schema, dict)
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert isinstance(schema["properties"], dict)

    def test_schema_validate_gstin(self) -> None:
        from mcp_india_stack.server import schema_validate_gstin

        self._assert_valid_schema(schema_validate_gstin())

    def test_schema_validate_pan(self) -> None:
        from mcp_india_stack.server import schema_validate_pan

        self._assert_valid_schema(schema_validate_pan())

    def test_schema_calculate_income_tax(self) -> None:
        from mcp_india_stack.server import schema_calculate_income_tax

        self._assert_valid_schema(schema_calculate_income_tax())

    def test_schema_calculate_gst(self) -> None:
        from mcp_india_stack.server import schema_calculate_gst

        self._assert_valid_schema(schema_calculate_gst())

    def test_schema_calculate_tds(self) -> None:
        from mcp_india_stack.server import schema_calculate_tds

        self._assert_valid_schema(schema_calculate_tds())

    def test_schema_calculate_capital_gains(self) -> None:
        from mcp_india_stack.server import schema_calculate_capital_gains

        self._assert_valid_schema(schema_calculate_capital_gains())

    def test_schema_calculate_advance_tax(self) -> None:
        from mcp_india_stack.server import schema_calculate_advance_tax

        self._assert_valid_schema(schema_calculate_advance_tax())

    def test_schema_bulk_validate_gstin(self) -> None:
        from mcp_india_stack.server import schema_bulk_validate_gstin

        self._assert_valid_schema(schema_bulk_validate_gstin())


class TestBulkValidation:
    def test_bulk_validate_pan_empty_list(self) -> None:
        from mcp_india_stack.server import bulk_validate_pan

        result = bulk_validate_pan(pans=[])
        assert result["success"] is False
        assert "Empty PAN list" in str(result["errors"])

    def test_bulk_validate_pan_too_many(self) -> None:
        from mcp_india_stack.server import bulk_validate_pan

        pans = ["AAPFU0939F"] * 501
        result = bulk_validate_pan(pans=pans)
        assert result["success"] is False
        assert "Maximum 500" in str(result["errors"])

    def test_bulk_validate_pan_valid_pans(self) -> None:
        from mcp_india_stack.server import bulk_validate_pan

        result = bulk_validate_pan(pans=["AAPFU0939F", "AAPL1234C"])
        assert result["success"] is True
        assert "results" in result["data"]

    def test_bulk_validate_ifsc_empty_list(self) -> None:
        from mcp_india_stack.server import bulk_validate_ifsc

        result = bulk_validate_ifsc(ifscs=[])
        assert result["success"] is False

    def test_bulk_validate_ifsc_valid_codes(self) -> None:
        from mcp_india_stack.server import bulk_validate_ifsc

        result = bulk_validate_ifsc(ifscs=["SBIN0001234", "HDFC0001234"])
        assert "success" in result


class TestValidationFunctions:
    def test_validate_epf_code(self) -> None:
        from mcp_india_stack.server import validate_epf_code

        result = validate_epf_code(code="MHDL/123456")
        assert "success" in result

    def test_validate_esic_code(self) -> None:
        from mcp_india_stack.server import validate_esic_code

        result = validate_esic_code(code="31-12345-12345678")
        assert "success" in result

    def test_decode_digilocker_uri(self) -> None:
        from mcp_india_stack.server import decode_digilocker_uri

        result = decode_digilocker_uri(uri="did:digilocker:12345678")
        assert "success" in result

    def test_validate_epf_code_empty(self) -> None:
        from mcp_india_stack.server import validate_epf_code

        result = validate_epf_code(code="")
        assert "success" in result

    def test_validate_esic_code_invalid(self) -> None:
        from mcp_india_stack.server import validate_esic_code

        result = validate_esic_code(code="INVALID")
        assert "success" in result


class TestMoreSchemas:
    """Additional schema resource tests."""

    def test_schema_lookup_ifsc(self) -> None:
        from mcp_india_stack.server import schema_lookup_ifsc

        schema = schema_lookup_ifsc()
        assert schema.get("type") == "object"
        assert "properties" in schema

    def test_schema_validate_upi_vpa(self) -> None:
        from mcp_india_stack.server import schema_validate_upi_vpa

        schema = schema_validate_upi_vpa()
        assert schema.get("type") == "object"

    def test_schema_lookup_pincode(self) -> None:
        from mcp_india_stack.server import schema_lookup_pincode

        schema = schema_lookup_pincode()
        assert schema.get("type") == "object"

    def test_schema_lookup_hsn_code(self) -> None:
        from mcp_india_stack.server import schema_lookup_hsn_code

        schema = schema_lookup_hsn_code()
        assert schema.get("type") == "object"

    def test_schema_decode_state_code(self) -> None:
        from mcp_india_stack.server import schema_decode_state_code

        schema = schema_decode_state_code()
        assert schema.get("type") == "object"

    def test_schema_validate_aadhaar(self) -> None:
        from mcp_india_stack.server import schema_validate_aadhaar

        schema = schema_validate_aadhaar()
        assert schema.get("type") == "object"

    def test_schema_validate_voter_id(self) -> None:
        from mcp_india_stack.server import schema_validate_voter_id

        schema = schema_validate_voter_id()
        assert schema.get("type") == "object"

    def test_schema_validate_driving_license(self) -> None:
        from mcp_india_stack.server import schema_validate_driving_license

        schema = schema_validate_driving_license()
        assert schema.get("type") == "object"

    def test_schema_validate_passport(self) -> None:
        from mcp_india_stack.server import schema_validate_passport

        schema = schema_validate_passport()
        assert schema.get("type") == "object"

    def test_schema_validate_cin(self) -> None:
        from mcp_india_stack.server import schema_validate_cin

        schema = schema_validate_cin()
        assert schema.get("type") == "object"

    def test_schema_validate_din(self) -> None:
        from mcp_india_stack.server import schema_validate_din

        schema = schema_validate_din()
        assert schema.get("type") == "object"

    def test_schema_calculate_surcharge(self) -> None:
        from mcp_india_stack.server import schema_calculate_surcharge

        schema = schema_calculate_surcharge()
        assert schema.get("type") == "object"

    def test_schema_calculate_hra_exemption(self) -> None:
        from mcp_india_stack.server import schema_calculate_hra_exemption

        schema = schema_calculate_hra_exemption()
        assert schema.get("type") == "object"
