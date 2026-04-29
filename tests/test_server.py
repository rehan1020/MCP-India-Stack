"""Test server wrapper responses and new tools."""

import pytest


class TestServerResponses:
    def test_validate_gstin_response(self):
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin="27AAPFU0939F1ZV")
        assert result["success"] is True
        assert "confidence" in result
        assert "validated_by" in result
        assert result["confidence"] >= 0.65

    def test_validate_pan_response(self):
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan="AAPFU0939F")
        assert result["success"] is True
        assert "confidence" in result

    def test_lookup_ifsc_response(self):
        from mcp_india_stack.server import lookup_ifsc

        result = lookup_ifsc(ifsc_code="SBIN0001234")
        assert "confidence" in result

    def test_validate_upi_response(self):
        from mcp_india_stack.server import validate_upi_vpa

        result = validate_upi_vpa(vpa="test@okicici")
        assert "confidence" in result

    def test_lookup_pincode_response(self):
        from mcp_india_stack.server import lookup_pincode

        result = lookup_pincode(pincode="400001")
        assert "confidence" in result

    def test_lookup_hsn_response(self):
        from mcp_india_stack.server import lookup_hsn_code

        result = lookup_hsn_code(code="1001")
        assert "confidence" in result

    def test_validate_aadhaar_response(self):
        from mcp_india_stack.server import validate_aadhaar

        result = validate_aadhaar(aadhaar="123456789012")
        assert "confidence" in result

    def test_validate_cin_response(self):
        from mcp_india_stack.server import validate_cin

        result = validate_cin(cin="U67190TN2014PTC096249")
        assert "confidence" in result

    def test_validate_din_response(self):
        from mcp_india_stack.server import validate_din

        result = validate_din(din="00012345")
        assert "confidence" in result

    def test_calculate_income_tax_response(self):
        from mcp_india_stack.server import calculate_income_tax

        result = calculate_income_tax(gross_income=1500000)
        assert result["success"] is True

    def test_calculate_tds_response(self):
        from mcp_india_stack.server import calculate_tds

        result = calculate_tds(section="192", payment_amount=100000, pan_available=True)
        assert "data" in result

    def test_calculate_gst_response(self):
        from mcp_india_stack.server import calculate_gst

        result = calculate_gst(amount=1000, gst_rate=18, transaction_type="intra_state")
        assert "data" in result

    def test_calculate_surcharge_response(self):
        from mcp_india_stack.server import calculate_surcharge

        result = calculate_surcharge(total_income=5000000, base_tax=125000, regime="new")
        assert "data" in result


class TestNewServerTools:
    def test_bulk_validate_gstin(self):
        from mcp_india_stack.server import bulk_validate_gstin

        result = bulk_validate_gstin(gstins=["27AAPFU0939F1ZV", "27AAPFU0939F1ZV"])
        assert result["success"] is True
        assert len(result["data"]["results"]) == 2

    def test_bulk_validate_pan(self):
        from mcp_india_stack.server import bulk_validate_pan

        result = bulk_validate_pan(pans=["AAPFU0939F", "AAPFU0939F"])
        assert result["success"] is True

    def test_bulk_validate_ifsc(self):
        from mcp_india_stack.server import bulk_validate_ifsc

        result = bulk_validate_ifsc(ifscs=["SBIN0001234"])
        assert result["success"] is True

    def test_calculate_hra_exemption(self):
        from mcp_india_stack.server import calculate_hra_exemption

        result = calculate_hra_exemption(basic_salary=50000, hra_received=180000, rent_paid=240000)
        assert result["success"] is True

    def test_calculate_capital_gains(self):
        from mcp_india_stack.server import calculate_capital_gains

        result = calculate_capital_gains(
            sale_price=150000, purchase_price=100000, asset_type="equity"
        )
        assert result["success"] is True

    def test_calculate_advance_tax(self):
        from mcp_india_stack.server import calculate_advance_tax

        result = calculate_advance_tax(estimated_income=1500000)
        assert result["success"] is True

    def test_lookup_bbps_biller(self):
        from mcp_india_stack.server import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity")
        assert result["success"] is True

    def test_decode_pan_type(self):
        from mcp_india_stack.server import decode_pan_type

        result = decode_pan_type(pan="AAPFU0939F")
        assert result["success"] is True

    def test_lookup_bank(self):
        from mcp_india_stack.server import lookup_bank

        result = lookup_bank(name_or_code="SBIN")
        assert result["success"] is True

    def test_validate_epf_code(self):
        from mcp_india_stack.server import validate_epf_code

        result = validate_epf_code(code="MH/12345/67890/123")
        assert "data" in result

    def test_validate_esic_code(self):
        from mcp_india_stack.server import validate_esic_code

        result = validate_esic_code(code="12-12345-67890")
        assert "data" in result

    def test_decode_digilocker_uri(self):
        from mcp_india_stack.server import decode_digilocker_uri

        result = decode_digilocker_uri(uri="dlg://uidai/aadhaar")
        assert result["success"] is True

    def test_validate_fssai(self):
        from mcp_india_stack.server import validate_fssai

        result = validate_fssai(license_number="11223344556677")
        assert result["success"] is True


class TestServerResources:
    def test_server_status(self):
        from mcp_india_stack.server import server_status

        status = server_status()
        assert status["version"] == "0.3.0"
        assert status["tool_count"] == 30

    def test_changelog(self):
        from mcp_india_stack.server import changelog

        cl = changelog()
        assert cl["current_version"] == "0.3.0"
        assert len(cl["entries"]) > 0


class TestErrorHandling:
    def test_validate_gstin_error(self):
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin=None)
        assert result["success"] is False

    def test_validate_pan_error(self):
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan=None)
        assert result["success"] is False

    def test_lookup_ifsc_error(self):
        from mcp_india_stack.server import lookup_ifsc

        result = lookup_ifsc(ifsc_code=None)
        assert result["success"] is False


class TestMessyInputNormalization:
    def test_validate_gstin_messy_input_single_call(self):
        from mcp_india_stack.server import validate_gstin

        result = validate_gstin(gstin="27 aapfu 0939f 1zv")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["normalized_input"] == "27AAPFU0939F1ZV"

    def test_validate_pan_messy_input_single_call(self):
        from mcp_india_stack.server import validate_pan

        result = validate_pan(pan="aapf u0939f")
        assert result["success"] is True
        assert result["data"]["valid"] is True
        assert result["data"]["pan"] == "AAPFU0939F"

    def test_validate_aadhaar_messy_input_single_call(self):
        from mcp_india_stack.server import validate_aadhaar

        result = validate_aadhaar(aadhaar="2341 2341 2346")
        assert result["success"] is True
        assert result["data"]["valid"] is True
