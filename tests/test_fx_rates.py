"""Tests for the zero-auth INR FX tools (RBI reference, SBI TT, CBIC customs).

All HTTP traffic is mocked with respx; no test reaches the network.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

import mcp_india_stack.tools.fx_rates as fx
from mcp_india_stack.tools.fx_rates import cbic_customs_rate, inr_reference_rate, sbi_tt_rate
from mcp_india_stack.tools.ifsc import _CircuitBreaker

RBI_URL = f"{fx._FX_BASE_URL}/central-bank/rbi"
CBIC_URL = f"{fx._FX_BASE_URL}/central-bank/cbic"
SBI_URL = f"{fx._FX_BASE_URL}/bank-rates/in/sbi"

RBI_PAYLOAD: dict[str, Any] = {
    "bank": "rbi",
    "rate_date": "2026-11-03",
    "age_days": 0,
    "stale": False,
    "cadence": "daily",
    "rates": [
        {"base": "EUR", "quote": "INR", "type": "reference", "value": 106.1398},
        {"base": "USD", "quote": "INR", "type": "reference", "value": 94.8606},
    ],
}

CBIC_PAYLOAD: dict[str, Any] = {
    "bank": "cbic",
    "rate_date": "2026-10-16",
    "age_days": 18,
    "stale": False,
    "cadence": "fortnightly",
    "rates": [
        {"base": "USD", "quote": "INR", "type": "export", "value": 94.1},
        {"base": "USD", "quote": "INR", "type": "import", "value": 95.9},
        {"base": "EUR", "quote": "INR", "type": "import", "value": 108.55},
    ],
}

SBI_PAYLOAD: dict[str, Any] = {
    "bank": "sbi",
    "name": "State Bank of India",
    "quote_ccy": "INR",
    "bank_updated_at": "03-11-2026 Time 9:04 AM",
    "basis": "Telegraphic transfer",
    "captured_at": "2026-11-03T18:09:52.712Z",
    "ccy": "USD",
    "buy": 94.32,
    "sell": 95.17,
    "mid": 94.745,
}


@pytest.fixture(autouse=True)
def _fresh_breaker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts with a closed circuit breaker."""
    monkeypatch.setattr(fx, "_fx_breaker", _CircuitBreaker(5, 30.0))


# ---------------------------------------------------------------------------
# Input validation (no HTTP)
# ---------------------------------------------------------------------------
@respx.mock
@pytest.mark.parametrize("bad", ["", "  ", "US", "USDX", "us1", None])
def test_invalid_currency_rejected_without_network(bad: str | None) -> None:
    route = respx.get(url__startswith=fx._FX_BASE_URL)
    for fn in (inr_reference_rate, sbi_tt_rate, cbic_customs_rate):
        result = fn(bad)  # type: ignore[arg-type]
        assert result["success"] is False
        assert result["value"] is None
        assert result["quote"] == "INR"
        assert result["errors"]
    assert not route.called


@respx.mock
def test_cbic_invalid_type_rejected_without_network() -> None:
    route = respx.get(CBIC_URL)
    result = cbic_customs_rate("USD", type="transit")
    assert result["success"] is False
    assert result["errors"] == ["type must be 'import' or 'export'"]
    assert not route.called


# ---------------------------------------------------------------------------
# RBI reference rate
# ---------------------------------------------------------------------------
@respx.mock
def test_inr_reference_rate_success_and_case_normalisation() -> None:
    route = respx.get(RBI_URL).mock(return_value=httpx.Response(200, json=RBI_PAYLOAD))
    result = inr_reference_rate("usd")
    assert route.called
    assert result["success"] is True
    assert result["currency"] == "USD"
    assert result["quote"] == "INR"
    assert result["value"] == 94.8606
    assert result["rate_date"] == "2026-11-03"
    assert result["rate_type"] == "reference"
    assert result["source"] == "rbi_reference_rate"
    assert result["source_url"] == RBI_URL
    assert result["errors"] == []
    assert result["warnings"] == []


@respx.mock
def test_inr_reference_rate_currency_not_published() -> None:
    respx.get(RBI_URL).mock(return_value=httpx.Response(200, json=RBI_PAYLOAD))
    result = inr_reference_rate("CHF")
    assert result["success"] is False
    assert result["value"] is None
    assert result["rate_date"] == "2026-11-03"
    assert result["errors"][0] == "no reference rate published for CHF"
    assert result["errors"][1] == "available: EUR, USD"


@respx.mock
def test_inr_reference_rate_stale_table_warns() -> None:
    stale = dict(RBI_PAYLOAD, stale=True, age_days=4)
    respx.get(RBI_URL).mock(return_value=httpx.Response(200, json=stale))
    result = inr_reference_rate("USD")
    assert result["success"] is True
    assert result["warnings"] == ["rate table flagged stale by source (age_days=4)"]


@respx.mock
def test_inr_reference_rate_table_404_reports_upstream_message() -> None:
    respx.get(RBI_URL).mock(
        return_value=httpx.Response(404, json={"error": "No published table available"})
    )
    result = inr_reference_rate("USD")
    assert result["success"] is False
    assert result["errors"] == ["No published table available"]
    assert fx._fx_breaker.is_open is False


@respx.mock
def test_inr_reference_rate_unexpected_shape() -> None:
    respx.get(RBI_URL).mock(return_value=httpx.Response(200, json={"bank": "rbi"}))
    result = inr_reference_rate("USD")
    assert result["success"] is False
    assert result["errors"] == ["fx source returned an unexpected shape"]


# ---------------------------------------------------------------------------
# CBIC customs rate
# ---------------------------------------------------------------------------
@respx.mock
def test_cbic_customs_rate_import_default() -> None:
    respx.get(CBIC_URL).mock(return_value=httpx.Response(200, json=CBIC_PAYLOAD))
    result = cbic_customs_rate("USD")
    assert result["success"] is True
    assert result["rate_type"] == "import"
    assert result["value"] == 95.9
    assert result["rate_date"] == "2026-10-16"
    assert result["source"] == "cbic_customs_rate"


@respx.mock
def test_cbic_customs_rate_export_case_insensitive() -> None:
    respx.get(CBIC_URL).mock(return_value=httpx.Response(200, json=CBIC_PAYLOAD))
    result = cbic_customs_rate("usd", type=" Export ")
    assert result["success"] is True
    assert result["rate_type"] == "export"
    assert result["value"] == 94.1


@respx.mock
def test_cbic_customs_rate_type_not_published_for_currency() -> None:
    respx.get(CBIC_URL).mock(return_value=httpx.Response(200, json=CBIC_PAYLOAD))
    result = cbic_customs_rate("EUR", type="export")
    assert result["success"] is False
    assert result["errors"][0] == "no export rate published for EUR"
    assert result["errors"][1] == "available: USD"


# ---------------------------------------------------------------------------
# SBI TT rate
# ---------------------------------------------------------------------------
@respx.mock
def test_sbi_tt_rate_success() -> None:
    route = respx.get(SBI_URL, params={"ccy": "USD"}).mock(
        return_value=httpx.Response(200, json=SBI_PAYLOAD)
    )
    result = sbi_tt_rate("usd")
    assert route.called
    assert result["success"] is True
    assert result["currency"] == "USD"
    assert result["buy"] == 94.32
    assert result["sell"] == 95.17
    assert result["value"] == 94.745
    assert result["rate_date"] == "2026-11-03"
    assert result["bank_updated_at"] == "03-11-2026 Time 9:04 AM"
    assert result["basis"] == "Telegraphic transfer"
    assert result["rate_type"] == "tt"
    assert result["source"] == "sbi_tt_rate"
    assert result["source_url"] == f"{SBI_URL}?ccy=USD"
    assert result["errors"] == []
    assert result["warnings"] == ["indicative bank board rate, not an official or reference rate"]


@respx.mock
def test_sbi_tt_rate_currency_not_displayed_404() -> None:
    respx.get(SBI_URL, params={"ccy": "XXX"}).mock(
        return_value=httpx.Response(
            404, json={"error": "State Bank of India does not display a rate for XXX"}
        )
    )
    result = sbi_tt_rate("XXX")
    assert result["success"] is False
    assert result["errors"] == ["State Bank of India does not display a rate for XXX"]
    assert fx._fx_breaker.is_open is False


@respx.mock
def test_sbi_tt_rate_404_without_json_body() -> None:
    respx.get(SBI_URL, params={"ccy": "XXX"}).mock(return_value=httpx.Response(404, text="gone"))
    result = sbi_tt_rate("XXX")
    assert result["success"] is False
    assert result["errors"] == ["fx source returned 404"]


@respx.mock
def test_sbi_tt_rate_missing_buy_sell_is_unexpected_shape() -> None:
    respx.get(SBI_URL, params={"ccy": "USD"}).mock(
        return_value=httpx.Response(200, json={"bank": "sbi", "ccy": "USD"})
    )
    result = sbi_tt_rate("USD")
    assert result["success"] is False
    assert result["errors"] == ["fx source returned an unexpected shape"]


@respx.mock
def test_sbi_tt_rate_missing_captured_at_gives_null_date() -> None:
    payload = {k: v for k, v in SBI_PAYLOAD.items() if k != "captured_at"}
    respx.get(SBI_URL, params={"ccy": "USD"}).mock(return_value=httpx.Response(200, json=payload))
    result = sbi_tt_rate("USD")
    assert result["success"] is True
    assert result["rate_date"] is None


# ---------------------------------------------------------------------------
# Unavailability and circuit breaker
# ---------------------------------------------------------------------------
@respx.mock
def test_timeout_is_reported_not_raised() -> None:
    route = respx.get(RBI_URL).mock(side_effect=httpx.TimeoutException("timed out"))
    result = inr_reference_rate("USD")
    assert route.called
    assert result["success"] is False
    assert result["errors"] == ["fx source unavailable or timed out"]


@respx.mock
def test_server_error_is_reported() -> None:
    respx.get(CBIC_URL).mock(return_value=httpx.Response(503))
    result = cbic_customs_rate("USD")
    assert result["success"] is False
    assert result["errors"] == ["fx source returned 503"]


@respx.mock
def test_non_json_200_is_reported() -> None:
    respx.get(RBI_URL).mock(return_value=httpx.Response(200, text="<html>maintenance</html>"))
    result = inr_reference_rate("USD")
    assert result["success"] is False
    assert result["errors"] == ["fx source returned a non-JSON body"]


@respx.mock
def test_breaker_trips_after_threshold_and_skips_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fx, "_fx_breaker", _CircuitBreaker(2, 60.0))
    route = respx.get(RBI_URL).mock(return_value=httpx.Response(500))

    assert inr_reference_rate("USD")["errors"] == ["fx source returned 500"]
    assert inr_reference_rate("USD")["errors"] == ["fx source returned 500"]
    assert route.call_count == 2
    assert fx._fx_breaker.is_open is True

    # Breaker is shared by all three tools; none of them should hit the network now.
    for fn in (inr_reference_rate, sbi_tt_rate, cbic_customs_rate):
        result = fn("USD")
        assert result["success"] is False
        assert result["errors"] == ["fx source unavailable: circuit_open"]
    assert route.call_count == 2


@respx.mock
def test_breaker_resets_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fx, "_fx_breaker", _CircuitBreaker(3, 60.0))
    rbi = respx.get(RBI_URL)
    rbi.mock(return_value=httpx.Response(500))
    inr_reference_rate("USD")
    inr_reference_rate("USD")
    rbi.mock(return_value=httpx.Response(200, json=RBI_PAYLOAD))
    assert inr_reference_rate("USD")["success"] is True
    rbi.mock(return_value=httpx.Response(500))
    inr_reference_rate("USD")
    inr_reference_rate("USD")
    assert fx._fx_breaker.is_open is False


# ---------------------------------------------------------------------------
# Registration wrappers and tiers
# ---------------------------------------------------------------------------
def test_tools_registered_as_lookup_live() -> None:
    import mcp_india_stack.registrations  # noqa: F401
    from mcp_india_stack.app import TOOL_TIERS, mcp
    from mcp_india_stack.permission_tiers import PermissionTier

    registered = mcp._tool_manager._tools
    for name in ("inr_reference_rate", "sbi_tt_rate", "cbic_customs_rate"):
        assert TOOL_TIERS[name] is PermissionTier.LOOKUP_LIVE
        tool = registered[name]
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.openWorldHint is True
        assert tool.parameters["required"] == ["currency"]


@respx.mock
def test_registration_wrappers_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_india_stack.registrations import markets

    respx.get(RBI_URL).mock(return_value=httpx.Response(200, json=RBI_PAYLOAD))
    respx.get(CBIC_URL).mock(return_value=httpx.Response(200, json=CBIC_PAYLOAD))
    respx.get(SBI_URL, params={"ccy": "USD"}).mock(
        return_value=httpx.Response(200, json=SBI_PAYLOAD)
    )
    assert markets.inr_reference_rate(currency="USD")["value"] == 94.8606
    assert markets.sbi_tt_rate(currency="USD")["buy"] == 94.32
    assert markets.cbic_customs_rate(currency="USD", type="export")["value"] == 94.1
