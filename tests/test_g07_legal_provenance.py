"""Tests for G7: Legal data provenance, crosswalks, and limitation edge cases."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_india_stack.tools.bare_act import (
    decode_ipc_bns_crosswalk,
    lookup_bns_section,
    lookup_bnss_section,
    lookup_bsa_section,
    lookup_crpc_section,
    lookup_evidence_act_section,
    lookup_ipc_section,
)
from mcp_india_stack.tools.court_fee import calculate_court_fee
from mcp_india_stack.tools.limitation import calculate_limitation_deadline
from mcp_india_stack.tools.stamp_duty import calculate_stamp_duty

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "mcp_india_stack" / "data"


class TestDatasetProvenance:
    """Every dataset file in data/legal and data/rti must contain source_ref and last_verified."""

    def test_court_fees_provenance(self) -> None:
        path = DATA_DIR / "legal" / "court_fees.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 10
        for state, details in data.items():
            assert "source_ref" in details, f"Missing source_ref in court_fees state {state}"
            assert "last_verified" in details, f"Missing last_verified in court_fees state {state}"
            assert details["source_ref"].strip() != ""
            assert details["last_verified"].startswith("202")

    def test_stamp_duty_provenance(self) -> None:
        path = DATA_DIR / "legal" / "stamp_duty.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 10
        for state, details in data.items():
            assert "source_ref" in details, f"Missing source_ref in stamp_duty state {state}"
            assert "last_verified" in details, f"Missing last_verified in stamp_duty state {state}"
            assert details["source_ref"].strip() != ""
            assert details["last_verified"].startswith("202")

    def test_court_establishments_provenance(self) -> None:
        path = DATA_DIR / "legal" / "court_establishments.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) > 0
        for code, details in data.items():
            assert "source_ref" in details, f"Missing source_ref in establishment {code}"
            assert "last_verified" in details, f"Missing last_verified in establishment {code}"

    def test_limitation_periods_provenance(self) -> None:
        path = DATA_DIR / "legal" / "limitation_periods.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) > 0
        for item in data:
            assert "source_ref" in item, f"Missing source_ref in article {item.get('article')}"
            assert "last_verified" in item, (
                f"Missing last_verified in article {item.get('article')}"
            )
            assert item["source_ref"].startswith("Limitation Act")

    def test_bare_acts_provenance(self) -> None:
        path = DATA_DIR / "legal" / "bare_acts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) >= 15
        for item in data:
            act_sec = f"{item.get('act')} {item.get('section')}"
            assert "source_ref" in item, f"Missing source_ref in {act_sec}"
            assert "last_verified" in item, f"Missing last_verified in {act_sec}"

    def test_rti_fees_provenance(self) -> None:
        path = DATA_DIR / "rti" / "rti_fees.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "central" in data
        assert "source_ref" in data["central"]
        assert "last_verified" in data["central"]
        for st, details in data.get("states", {}).items():
            assert "source_ref" in details, f"Missing source_ref in RTI state {st}"
            assert "last_verified" in details, f"Missing last_verified in RTI state {st}"


class TestUnsupportedStates:
    """Court fee and stamp duty for unsupported states return unsupported_state."""

    def test_court_fee_unsupported_state(self) -> None:
        res = calculate_court_fee("GA", 500000.0, "money")
        assert res.get("error") == "unsupported_state"
        assert "unsupported_state" in res.get("errors", [])
        assert res.get("coverage") == "partial"
        assert isinstance(res.get("supported_states"), list)
        assert "MH" in res["supported_states"]
        assert "DL" in res["supported_states"]
        assert "fee_amount" not in res or res.get("fee_amount") is None

    def test_stamp_duty_unsupported_state(self) -> None:
        res = calculate_stamp_duty("GA", "sale_deed", 1000000.0)
        assert res.get("error") == "unsupported_state"
        assert "unsupported_state" in res.get("errors", [])
        assert res.get("coverage") == "partial"
        assert isinstance(res.get("supported_states"), list)
        assert "MH" in res["supported_states"]
        assert "duty_amount" not in res or res.get("duty_amount") is None

    def test_supported_state_court_fee_and_stamp_duty(self) -> None:
        cf = calculate_court_fee("MH", 100000.0, "money")
        assert cf.get("fee_amount") == 3000.0
        assert cf.get("coverage") == "partial"
        assert cf.get("source_ref") != ""
        assert "MH" in cf.get("supported_states", [])

        sd = calculate_stamp_duty("MH", "sale_deed", 10000000.0)
        assert sd.get("duty_amount") == 500000.0
        assert sd.get("coverage") == "partial"
        assert sd.get("source_ref") != ""


class TestCrosswalkRoundTrips:
    """Round-trip tests for IPC<->BNS, CrPC<->BNSS, IEA<->BSA with explicit one-to-many flagging."""

    def test_ipc_bns_round_trip_murder(self) -> None:
        forward = decode_ipc_bns_crosswalk("302", from_act="IPC")
        assert forward.get("success") is True
        assert forward.get("target_section") == "103"
        assert forward.get("is_one_to_many") is False
        assert forward.get("source_ref") != ""

        reverse = decode_ipc_bns_crosswalk("103", from_act="BNS")
        assert reverse.get("success") is True
        assert reverse.get("target_section") == "302"
        assert reverse.get("is_one_to_many") is False

    def test_crpc_bnss_round_trip_fir(self) -> None:
        forward = decode_ipc_bns_crosswalk("154", from_act="CrPC")
        assert forward.get("success") is True
        assert forward.get("target_section") == "173"
        assert forward.get("source_ref") != ""

        reverse = decode_ipc_bns_crosswalk("173", from_act="BNSS")
        assert reverse.get("success") is True
        assert reverse.get("target_section") == "154"

    def test_iea_bsa_round_trip_electronic_evidence(self) -> None:
        forward = decode_ipc_bns_crosswalk("65B", from_act="IEA")
        assert forward.get("success") is True
        assert forward.get("target_section") == "63"
        assert forward.get("source_ref") != ""

        reverse = decode_ipc_bns_crosswalk("63", from_act="BSA")
        assert reverse.get("success") is True
        assert reverse.get("target_section") == "65B"

    def test_one_to_many_flagging_rape(self) -> None:
        res = decode_ipc_bns_crosswalk("376", from_act="IPC")
        assert res.get("success") is True
        assert res.get("is_one_to_many") is True
        target_sections = res.get("target_sections", [])
        assert "64" in target_sections
        assert len(target_sections) > 1

    def test_bare_act_bidirectional_lookups(self) -> None:
        ipc = lookup_ipc_section("302")
        assert ipc.get("bns_crosswalk") == "103"
        assert ipc.get("source_ref") != ""

        bns = lookup_bns_section("103")
        assert bns.get("ipc_crosswalk") == "302"
        assert bns.get("source_ref") != ""

        crpc = lookup_crpc_section("154")
        assert crpc.get("bnss_crosswalk") == "173"

        bnss = lookup_bnss_section("173")
        assert bnss.get("crpc_crosswalk") == "154"

        iea = lookup_evidence_act_section("65B")
        assert iea.get("bsa_crosswalk") == "63"

        bsa = lookup_bsa_section("63")
        assert bsa.get("iea_crosswalk") == "65B"


class TestLimitationEdgeCases:
    """Limitation-deadline edge cases: leap day, month-end, Section 4 and Section 12."""

    def test_leap_day_non_leap_year_rollover(self) -> None:
        # Cause of action on leap day 2024-02-29; 3 years limitation -> lands on 2027-02-28
        res = calculate_limitation_deadline("payment of money", "2024-02-29")
        match = res["matches"][0]
        assert match["limitation_years"] == 3
        assert match["deadline_date"] == "2027-02-28"
        assert match["original_deadline_date"] == "2027-02-28"
        assert match["section_4_applied"] is False
        assert match["section_12_applied"] is False

    def test_leap_day_four_year_anniversary(self) -> None:
        # Mortgages / 12 years from 2024-02-29 lands on 2036-02-29 (2036 is a leap year)
        res = calculate_limitation_deadline("mortgage", "2024-02-29")
        match = [m for m in res["matches"] if m["limitation_years"] == 12][0]
        assert match["deadline_date"] == "2036-02-29"

    def test_month_end_consistency(self) -> None:
        # Cause of action on 2023-01-31; 3 years limitation -> 2026-01-31
        res = calculate_limitation_deadline("payment of money", "2023-01-31")
        match = res["matches"][0]
        assert match["deadline_date"] == "2026-01-31"

    def test_section_12_certified_copy_exclusion(self) -> None:
        # Section 12: 14 days spent obtaining certified copy
        res = calculate_limitation_deadline("payment of money", "2024-01-15", exclusion_days=14)
        match = res["matches"][0]
        # Base 3 years from 2024-01-15 is 2027-01-15; +14 days = 2027-01-29
        assert match["original_deadline_date"] == "2027-01-29"
        assert match["deadline_date"] == "2027-01-29"
        assert match["section_12_applied"] is True
        assert match["section_12_exclusion_days"] == 14

    def test_section_4_court_closed_with_explicit_reopen_date(self) -> None:
        # Court closed on deadline, reopens 2027-01-18
        res = calculate_limitation_deadline(
            "payment of money",
            "2024-01-15",
            court_closed_on_deadline=True,
            court_reopen_date="2027-01-18",
        )
        match = res["matches"][0]
        assert match["original_deadline_date"] == "2027-01-15"
        assert match["deadline_date"] == "2027-01-18"
        assert match["section_4_applied"] is True

    def test_section_4_court_closed_weekend_extension(self) -> None:
        # Base deadline 2027-01-15 is Friday; if closed, advances to next day or Monday
        res = calculate_limitation_deadline(
            "payment of money",
            "2024-01-15",
            court_closed_on_deadline=True,
        )
        match = res["matches"][0]
        assert match["section_4_applied"] is True
        assert match["deadline_date"] > "2027-01-15"
