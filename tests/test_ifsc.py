import httpx
import respx
from pytest import MonkeyPatch

from mcp_india_stack.tools.ifsc import lookup_ifsc


def test_lookup_ifsc_format_validation() -> None:
    result = lookup_ifsc("bad")
    assert result["found"] is False
    assert result["errors"]


def test_lookup_ifsc_not_found_shape() -> None:
    result = lookup_ifsc("ABCD0123456")
    assert "found" in result


@respx.mock
def test_lookup_ifsc_live_fallback_success(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("mcp_india_stack.tools.ifsc.load_ifsc_index", lambda: {})
    route = respx.get("https://ifsc.razorpay.com/ZZZZ0123456").mock(
        return_value=httpx.Response(
            200,
            json={
                "BANK": "Test Bank",
                "BRANCH": "Main",
                "ADDRESS": "Addr",
                "CITY": "Mumbai",
                "DISTRICT": "Mumbai",
                "STATE": "Maharashtra",
                "MICR": "400000001",
                "UPI": True,
                "RTGS": True,
                "NEFT": True,
                "IMPS": True,
                "SWIFT": "TESTINBB",
            },
        )
    )

    result = lookup_ifsc("ZZZZ0123456")
    assert route.called
    assert result["found"] is True
    assert result["source"] == "live_api"
    assert result["bank"] == "Test Bank"


@respx.mock
def test_lookup_ifsc_live_fallback_timeout(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("mcp_india_stack.tools.ifsc.load_ifsc_index", lambda: {})
    route = respx.get("https://ifsc.razorpay.com/ZZZX0123456").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    result = lookup_ifsc("ZZZX0123456")
    assert route.called
    assert result["found"] is False
    assert "IFSC not found in local dataset" in result["errors"]
    assert "Live IFSC fallback failed or timed out" in result["warnings"]
