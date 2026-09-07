"""Tests for legal reference tools."""

from __future__ import annotations

from mcp_india_stack.tools.bare_act import (
    decode_ipc_bns_crosswalk,
    lookup_bns_section,
    lookup_crpc_section,
    lookup_evidence_act_section,
    lookup_ipc_section,
)
from mcp_india_stack.tools.cnr import decode_cnr_number
from mcp_india_stack.tools.court_establishment import lookup_court_establishment_code
from mcp_india_stack.tools.court_fee import calculate_court_fee
from mcp_india_stack.tools.limitation import calculate_limitation_deadline
from mcp_india_stack.tools.stamp_duty import calculate_stamp_duty


class TestCnrDecoder:
    def test_valid_cnr(self) -> None:
        result = decode_cnr_number("DLCT010012342024")
        assert result.get("is_structurally_valid") is True
        assert result.get("state_code") == "DL"
        assert result.get("court_establishment_code") == "DLCT"
        assert result.get("filing_year") == "2024"

    def test_short_cnr(self) -> None:
        result = decode_cnr_number("DLCT01")
        assert len(result.get("errors", [])) > 0

    def test_empty_cnr(self) -> None:
        result = decode_cnr_number("")
        assert len(result.get("errors", [])) > 0


class TestCourtEstablishment:
    def test_known_code(self) -> None:
        result = lookup_court_establishment_code("DLCT")
        assert result.get("success") is True
        assert "court_name" in result

    def test_unknown_code(self) -> None:
        result = lookup_court_establishment_code("ZZZZ")
        assert result.get("success") is False


class TestBareActLookup:
    def test_ipc_section_302(self) -> None:
        result = lookup_ipc_section("302")
        assert "murder" in result.get("title", "").lower()

    def test_ipc_section_420(self) -> None:
        result = lookup_ipc_section("420")
        assert "cheat" in result.get("title", "").lower()

    def test_bns_section_exists(self) -> None:
        result = lookup_bns_section("103")
        assert result.get("success") is True

    def test_unknown_section(self) -> None:
        result = lookup_ipc_section("99999")
        assert result.get("success") is False

    def test_crpc_section(self) -> None:
        result = lookup_crpc_section("154")
        assert result.get("success") is True

    def test_evidence_act(self) -> None:
        result = lookup_evidence_act_section("65B")
        assert result.get("success") is True


class TestIpcBnsCrosswalk:
    def test_ipc_to_bns(self) -> None:
        result = decode_ipc_bns_crosswalk("302", from_act="IPC")
        assert result.get("success") is True
        assert "target_section" in result

    def test_unknown_crosswalk(self) -> None:
        result = decode_ipc_bns_crosswalk("99999", from_act="IPC")
        assert result.get("success") is False


class TestLimitation:
    def test_money_recovery(self) -> None:
        result = calculate_limitation_deadline("payment of money", "2024-01-15")
        assert result.get("matches")[0]["limitation_years"] == 3
        assert "deadline_date" in result.get("matches")[0]

    def test_unknown_suit_type(self) -> None:
        result = calculate_limitation_deadline("xyzabc", "2024-01-15")
        assert len(result.get("errors", [])) > 0 or not result.get("matched_articles")


class TestCourtFee:
    def test_maharashtra_money_suit(self) -> None:
        result = calculate_court_fee("MH", 500000.0, "money")
        assert result.get("fee_amount", 0) > 0 or result.get("calculation_basis")

    def test_unknown_state(self) -> None:
        result = calculate_court_fee("ZZ", 100000.0)
        assert len(result.get("errors", [])) > 0

    def test_declaration_suit(self) -> None:
        result = calculate_court_fee("DL", 0.0, "declaration")
        assert result.get("fee_amount", -1) >= 0


class TestStampDuty:
    def test_maharashtra_sale_deed(self) -> None:
        result = calculate_stamp_duty("MH", "sale_deed", 8000000.0)
        assert result.get("duty_amount", 0) > 0
        assert result.get("total_payable", 0) > 0

    def test_unknown_state(self) -> None:
        result = calculate_stamp_duty("ZZ", "sale_deed", 100000.0)
        assert len(result.get("errors", [])) > 0

    def test_unknown_instrument(self) -> None:
        result = calculate_stamp_duty("MH", "unknown_type", 100000.0)
        assert len(result.get("errors", [])) > 0
