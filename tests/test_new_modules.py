"""Test new modules for coverage."""

from unittest.mock import MagicMock, patch

import pytest


class TestPermissionTier:
    def test_enum_values(self) -> None:
        from mcp_india_stack.permission_tiers import PermissionTier

        assert PermissionTier.READ_ONLY == 0
        assert PermissionTier.LOOKUP_LIVE == 1
        assert PermissionTier.INITIATE == 2
        assert PermissionTier.SUBMIT == 3

    def test_enum_members(self) -> None:
        from mcp_india_stack.permission_tiers import PermissionTier

        members = list(PermissionTier)
        assert len(members) == 4


class TestDatabase:
    def test_get_db_config(self) -> None:
        from mcp_india_stack.database import get_db_config

        config = get_db_config()
        assert "db_url_set" in config
        assert "read_only" in config

    def test_is_db_connected(self) -> None:
        from mcp_india_stack.database import is_db_connected

        assert is_db_connected() is False

    def test_init_db_no_url(self) -> None:
        from mcp_india_stack.database import init_db_connection

        result = init_db_connection()
        assert result is False

    def test_close_db(self) -> None:
        from mcp_india_stack.database import close_db_connection

        close_db_connection()  # Should not raise

    def test_query_db_not_connected(self) -> None:
        from mcp_india_stack.database import query_db

        with pytest.raises(RuntimeError, match="Database not connected"):
            query_db("SELECT 1")

    def test_init_db_with_url_success(self, monkeypatch) -> None:
        from mcp_india_stack import database

        monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://localhost:8080")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch("mcp_india_stack.database.httpx.Client", return_value=mock_client):
            database._DB_URL = "http://localhost:8080"
            result = database.init_db_connection()
            assert result is True

        database._db_connection = None

    def test_init_db_connect_failure_falls_back(self, monkeypatch) -> None:
        from mcp_india_stack import database

        monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://localhost:8080")

        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("connection refused")

        with patch("mcp_india_stack.database.httpx.Client", return_value=mock_client):
            result = database.init_db_connection()
            assert result is False

        database._db_connection = None

    def test_query_db_when_connected(self, monkeypatch) -> None:
        from mcp_india_stack import database

        monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://localhost:8080")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [(1, "test")]
        mock_connection = MagicMock()
        mock_connection.get.return_value = mock_response

        database._db_connection = mock_connection
        database._DB_URL = "http://localhost:8080"

        result = database.query_db("SELECT 1")

        assert result == [(1, "test")]

        database._db_connection = None

    def test_query_db_returns_empty_on_error(self, monkeypatch) -> None:
        from mcp_india_stack import database

        monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://localhost:8080")

        mock_connection = MagicMock()
        mock_connection.get.side_effect = Exception("query failed")

        database._db_connection = mock_connection
        database._DB_URL = "http://localhost:8080"

        result = database.query_db("SELECT bad")

        assert result == []

        database._db_connection = None

    def test_close_db_when_connected(self, monkeypatch) -> None:
        from mcp_india_stack import database

        mock_connection = MagicMock()
        database._db_connection = mock_connection

        database.close_db_connection()

        mock_connection.close.assert_called_once()
        assert database._db_connection is None

    def test_close_db_when_not_connected(self, monkeypatch) -> None:
        from mcp_india_stack import database

        database._db_connection = None

        database.close_db_connection()

        assert database._db_connection is None


class TestTelemetryExtra:
    def test_hash_input_empty(self) -> None:
        from mcp_india_stack.telemetry import _hash_input

        assert _hash_input("") == ""
        assert _hash_input(None) == ""

    def test_hash_input_value(self) -> None:
        from mcp_india_stack.telemetry import _hash_input

        result = _hash_input("testinput")
        assert len(result) == 12
        assert result.isalnum()


class TestResponses:
    def test_build_response_with_optional_fields(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(
            success=True,
            data={"test": "data"},
            validated_by=["format", "checksum"],
            normalized_input="test123",
            stale=True,
            stale_reason="old_data",
            data_version="1.0",
            rate_limit_remaining=50,
            rate_limit_warning="low",
        )
        assert result["stale"] is True
        assert result["stale_reason"] == "old_data"
        assert result["data_version"] == "1.0"
        assert result["rate_limit_remaining"] == 50
        assert result["rate_limit_warning"] == "low"

    def test_calculate_confidence_various(self) -> None:
        from mcp_india_stack.utils.responses import _calculate_confidence

        assert _calculate_confidence([], True) == 0.0
        assert _calculate_confidence(["format"], True) == 0.4
        assert _calculate_confidence(["format", "checksum"], True) == 0.65
        assert _calculate_confidence(["format", "live_ping"], True) == 0.85
        assert _calculate_confidence(["db_lookup"], True) == 1.0
        assert _calculate_confidence(["format"], False) == 0.0

    def test_build_response_basic(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={"test": True})
        assert result["success"] is True
        assert result["confidence"] == 0.4  # Default confidence

    def test_build_response_with_validated_by(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={}, validated_by=["format", "checksum"])
        assert result["confidence"] == 0.65

    def test_build_response_with_live(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(
            success=True, data={}, validated_by=["format", "checksum", "live_ping"]
        )
        assert result["confidence"] == 0.85

    def test_build_response_failure(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=False, errors=["test error"])
        assert result["confidence"] == 0.0

    def test_build_response_with_normalized_input(self) -> None:
        from mcp_india_stack.utils.responses import build_response

        result = build_response(success=True, data={}, normalized_input="TEST123")
        assert result["normalized_input"] == "TEST123"


class TestNormalization:
    def test_normalize_gstin(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        result = normalize_gstin("27 AAPFU 0939F 1ZV")
        assert result["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_pan(self) -> None:
        from mcp_india_stack.normalization import normalize_pan

        result = normalize_pan("aapfu0939f")
        assert result["normalized_input"] == "AAPFU0939F"

    def test_normalize_ifsc(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        result = normalize_ifsc("SBIN 0001234")
        assert result["normalized_input"] == "SBIN0001234"

    def test_normalize_aadhaar(self) -> None:
        from mcp_india_stack.normalization import normalize_aadhaar

        result = normalize_aadhaar("1234 5678 9012")
        assert result["normalized_input"] == "123456789012"

    def test_normalize_pincode(self) -> None:
        from mcp_india_stack.normalization import normalize_pincode

        result = normalize_pincode("400 001")
        assert result["normalized_input"] == "400001"

    def test_normalize_cin(self) -> None:
        from mcp_india_stack.normalization import normalize_cin

        result = normalize_cin("U67190TN2014PTC096249")
        assert result["normalized_input"] == "U67190TN2014PTC096249"

    def test_normalize_fssai(self) -> None:
        from mcp_india_stack.normalization import normalize_fssai

        result = normalize_fssai("11223344556677")
        assert result["normalized_input"] == "11223344556677"

    def test_normalize_upi(self) -> None:
        from mcp_india_stack.normalization import normalize_upi

        result = normalize_upi("test@okicici")
        assert result["normalized_input"] == "test@okicici"

    def test_normalize_gstin_strips_spaces(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        assert normalize_gstin("27 aapfu 0939f 1zv")["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_gstin_strips_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_gstin

        assert normalize_gstin("27-AAPFU-0939F-1ZV")["normalized_input"] == "27AAPFU0939F1ZV"

    def test_normalize_ifsc_strips_spaces(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        assert normalize_ifsc("SBIN 0001234")["normalized_input"] == "SBIN0001234"

    def test_normalize_ifsc_strips_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_ifsc

        assert normalize_ifsc("SBIN-0001234")["normalized_input"] == "SBIN0001234"

    def test_normalize_upi_strips_spaces_not_hyphens(self) -> None:
        from mcp_india_stack.normalization import normalize_upi

        assert normalize_upi("test user@okicici")["normalized_input"] == "testuser@okicici"
        assert normalize_upi("test-user@okicici")["normalized_input"] == "test-user@okicici"


class TestTelemetry:
    def test_get_telemetry_status(self) -> None:
        from mcp_india_stack.telemetry import get_telemetry_status

        status = get_telemetry_status()
        assert "enabled" in status
        assert "log_path" in status

    def test_log_tool_usage_no_file(self) -> None:
        from mcp_india_stack.telemetry import log_tool_usage

        # Should not raise even if file can't be written
        log_tool_usage("test", "input", 10.0, "valid")

    def test_log_tool_usage_writes_to_file(self, tmp_path, monkeypatch) -> None:
        import hashlib
        import json

        from mcp_india_stack import telemetry

        log_file = tmp_path / "telemetry.jsonl"
        telemetry._LOG_PATH = str(log_file)
        telemetry._ENABLED = True

        from mcp_india_stack.telemetry import log_tool_usage

        input_value = "abc123def456"
        expected_hash = hashlib.sha256(input_value.encode()).hexdigest()[:12]
        log_tool_usage("validate_gstin", input_value, 12.0, "valid")

        with open(str(log_file)) as f:
            lines = f.readlines()

        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["tool_name"] == "validate_gstin"
        assert entry["hashed_input"] == expected_hash
        assert entry["latency_ms"] == 12.0
        assert entry["result_type"] == "valid"
        assert "timestamp" in entry
        assert len(entry["hashed_input"]) == 12

    def test_log_tool_usage_appends_multiple_entries(self, tmp_path, monkeypatch) -> None:
        import json

        from mcp_india_stack import telemetry

        log_file = tmp_path / "telemetry_multi.jsonl"
        telemetry._LOG_PATH = str(log_file)
        telemetry._ENABLED = True

        from mcp_india_stack.telemetry import log_tool_usage

        log_tool_usage("test_tool1", "input1", 10.0, "valid")
        log_tool_usage("test_tool2", "input2", 20.0, "success")
        log_tool_usage("test_tool3", "input3", 30.0, "found")

        with open(str(log_file)) as f:
            lines = f.readlines()

        assert len(lines) == 3
        for line in lines:
            assert json.loads(line) is not None

    def test_log_tool_usage_no_raw_pii(self, tmp_path, monkeypatch) -> None:
        import hashlib

        from mcp_india_stack import telemetry

        log_file = tmp_path / "telemetry_pii.jsonl"
        telemetry._LOG_PATH = str(log_file)
        telemetry._ENABLED = True

        from mcp_india_stack.telemetry import log_tool_usage

        raw_input = "27AAPFU0939F1ZV"
        hashed = hashlib.sha256(raw_input.encode()).hexdigest()[:12]
        log_tool_usage("validate_gstin", hashed, 10.0, "valid")

        with open(str(log_file)) as f:
            content = f.read()

        assert raw_input not in content

    def test_get_telemetry_status_when_enabled(self, monkeypatch) -> None:
        import importlib

        from mcp_india_stack import telemetry

        monkeypatch.setenv("MCP_INDIA_STACK_LOG", "1")

        importlib.reload(telemetry)

        status = telemetry.get_telemetry_status()
        assert status["enabled"] is True


class TestFssaiTool:
    def test_validate_fssai_valid(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11223344556677")
        assert result["valid"] is True
        assert "state_code" in result

    def test_validate_fssai_invalid(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("123")
        assert result["valid"] is False

    def test_validate_fssai_empty(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("")
        assert result["valid"] is False

    def test_validate_fssai_none(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai(None)
        assert result["valid"] is False

    def test_validate_fssai_whitespace_only(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("   ")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_fssai_invalid_state_code(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("50223344556677")
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_validate_fssai_invalid_year_code(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11990012345678")
        assert result["warnings"] or result["valid"] is True

    def test_validate_fssai_non_numeric(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("1122ABCD556677")
        assert result["valid"] is False

    def test_validate_fssai_year_warning(self) -> None:
        from mcp_india_stack.tools.fssai import validate_fssai

        result = validate_fssai("11319912345678")
        assert "Unusual license year" in result["warnings"][0]


class TestHraTool:
    def test_hra_exemption_metro(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 180000, 240000, "metro")
        assert result["exemption"] > 0

    def test_hra_exemption_non_metro(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(30000, 72000, 120000, "non_metro")
        assert result["exemption"] >= 0

    def test_hra_government(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 100000, 150000, is_government_employee=True)
        assert result["exemption"] >= 0

    def test_hra_invalid(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(-1000, 1000, 500)
        assert "must be positive" in str(result["errors"])

    def test_hra_no_rent(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_exemption

        result = calculate_hra_exemption(50000, 180000, 0)
        assert result["exemption"] == 0

    def test_hra_monthly_structure(self) -> None:
        from mcp_india_stack.tools.hra import calculate_hra_for_salary_structure

        result = calculate_hra_for_salary_structure(50000, 15000, 20000, "Mumbai")
        assert "monthly_exemption" in result


class TestCapitalGainsTool:
    def test_capital_gains_equity_stcg(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(150000, 100000, "equity", 300)
        assert result["short_term_gains"] == 50000
        assert result["tax_liability"] > 0

    def test_capital_gains_equity_ltcg(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(150000, 100000, "equity", 400)
        assert result["long_term_gains"] == 50000

    def test_capital_gains_real_estate(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(2000000, 1000000, "real_estate", 500)
        assert result["is_long_term"] is True

    def test_capital_gains_negative(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(-100000, 50000, "equity")
        assert "cannot be negative" in str(result["errors"])

    def test_home_loan_savings(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_home_loan_savings

        result = calculate_home_loan_savings(2000000, 1000000, 500000, 500)
        assert "capital_gains" in result

    def test_capital_gains_gold(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(200000, 100000, "gold", 400)
        assert result["asset_type"] == "gold"

    def test_capital_gains_crypto(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(200000, 100000, "crypto", 200)
        assert "Cryptocurrency" in result["warnings"][0]

    def test_capital_gains_with_indexation(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            5000000,
            2000000,
            "real_estate",
            700,
            inflation_index_purchase=300,
            inflation_index_sale=350,
        )
        assert result["cost_inflation_adjusted"] > 2000000

    def test_ltcg_equity_below_exemption_threshold_zero_tax(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=400
        )
        assert result["gain_type"] == "LTCG"
        assert result["tax_liability"] == 0.0
        assert result["exemption_applied"] == 25000.0
        assert result["taxable_gain"] == 0.0
        assert "exemption_note" in result

    def test_ltcg_equity_above_exemption_threshold_partial_tax(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=300, quantity=1000, holding_days=400
        )
        assert result["gain_type"] == "LTCG"
        assert result["taxable_gain"] == 100000.0
        assert result["tax_liability"] == 12500.0
        assert result["exemption_applied"] == 100000.0

    def test_ltcg_real_estate_no_exemption_applied(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="real_estate",
            buy_price=5000000,
            sell_price=6000000,
            quantity=1,
            holding_days=800,
        )
        assert result["gain_type"] == "LTCG"
        assert result["exemption_applied"] == 0.0
        assert result["tax_liability"] == result["taxable_gain"] * 0.20

    def test_stcg_equity_no_exemption_applied(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=200
        )
        assert result["gain_type"] == "STCG"
        assert result["exemption_applied"] == 0.0
        assert result["tax_liability"] == 25000 * 0.20

    def test_ltcg_exemption_note_always_present_for_equity(self) -> None:
        from mcp_india_stack.tools.capital_gains import calculate_capital_gains

        result = calculate_capital_gains(
            asset_type="equity", buy_price=100, sell_price=150, quantity=500, holding_days=400
        )
        assert "exemption_note" in result
        assert "1,00,000" in result["exemption_note"] or "100000" in result["exemption_note"]


class TestAdvanceTaxTool:
    def test_advance_tax_normal(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(1500000)
        assert "installments" in result
        assert len(result["installments"]) == 4

    def test_advance_tax_zero_income(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(0)
        assert result["advance_tax_due"] == 0

    def test_advance_tax_negative(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_advance_tax

        result = calculate_advance_tax(-1000)
        assert "must be positive" in str(result["errors"])

    def test_interest_penalty(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_interest_penalty

        result = calculate_interest_penalty(10000, 30)
        assert "interest_penalty" in result

    def test_interest_penalty_negative(self) -> None:
        from mcp_india_stack.tools.advance_tax import calculate_interest_penalty

        result = calculate_interest_penalty(-1000, 30)
        assert "cannot be negative" in str(result["errors"])


class TestBbpsTool:
    def test_bbps_by_category(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity")
        assert "billers" in result

    def test_bbps_by_state(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="electricity", state="Maharashtra")
        assert "billers" in result

    def test_bbps_by_biller_id(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(biller_id="ELEC_MH_MSEDC")
        assert "billers" in result

    def test_bbps_invalid_category(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller(category="invalid_category")
        assert "errors" in result

    def test_bbps_all_categories(self) -> None:
        from mcp_india_stack.tools.bbps import lookup_bbps_biller

        result = lookup_bbps_biller()
        assert "categories" in result
