"""Tests for RTI toolkit tools."""

from __future__ import annotations

from mcp_india_stack.tools.rti import (
    calculate_rti_deadline,
    calculate_rti_fee,
    calculate_rti_penalty_estimate,
    draft_first_appeal,
    draft_rti_application,
    draft_second_appeal,
)


class TestRtiFee:
    def test_central_fee(self) -> None:
        result = calculate_rti_fee("central", "general")
        assert result.get("application_fee") == 10

    def test_bpl_exempt(self) -> None:
        result = calculate_rti_fee("central", "bpl")
        assert result.get("bpl_exempt") is True
        assert result.get("application_fee") == 0 or result.get("fee_waived") is True

    def test_state_fee(self) -> None:
        result = calculate_rti_fee("MH", "general")
        assert result.get("application_fee", 0) > 0


class TestRtiDeadline:
    def test_standard_deadline(self) -> None:
        result = calculate_rti_deadline("2024-07-15")
        assert result.get("response_due_date") == "2024-08-14"

    def test_life_liberty_48h(self) -> None:
        result = calculate_rti_deadline("2024-07-15", concerns_life_or_liberty=True)
        assert result.get("response_due_date") == "2024-07-17"

    def test_apio_routing(self) -> None:
        result = calculate_rti_deadline("2024-07-15", routed_through_apio=True)
        assert result.get("response_due_date") == "2024-08-19"


class TestRtiPenalty:
    def test_penalty_within_cap(self) -> None:
        result = calculate_rti_penalty_estimate("2024-07-15", "2024-07-25")
        assert result.get("delay_days") == 10
        assert result.get("estimated_penalty") == 2500

    def test_penalty_capped(self) -> None:
        result = calculate_rti_penalty_estimate("2024-01-01", "2024-12-31")
        assert result.get("estimated_penalty") == 25000
        assert result.get("penalty_cap_reached") is True


class TestRtiDraft:
    def test_draft_application(self) -> None:
        result = draft_rti_application(
            "Ministry of Finance",
            "GST Collections",
            ["Total GST collected in FY2025-26"],
            "general",
        )
        draft_text = result.get("draft_text", "")
        assert "RTI" in draft_text
        assert "Section 6" in draft_text

    def test_draft_first_appeal(self) -> None:
        result = draft_first_appeal("RTI/2024/001", ["No response received"])
        draft_text = result.get("draft_text", "").lower()
        assert "appeal" in draft_text

    def test_draft_second_appeal(self) -> None:
        result = draft_second_appeal("RTI/2024/001", ["First appeal dismissed"])
        draft_text = result.get("draft_text", "").lower()
        assert "information commission" in draft_text
