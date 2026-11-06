"""Tests for yfinance market data hardening (G11).

Acceptance coverage:
- Empty frame
- Delisted or invalid symbol
- Malformed symbol (allowlist regex rejection)
- Timeout handling & backoff
- Partial data handling (missing fields without crashing)
- Upstream rate limit error mapping
- Short-TTL cache operation
- Additive output fields: data_source, delayed, as_of, experimental
- Experimental marker verification
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from mcp_india_stack.registrations.markets import (
    get_stock_history as reg_get_stock_history,
)
from mcp_india_stack.registrations.markets import (
    get_stock_quote as reg_get_stock_quote,
)
from mcp_india_stack.tools.market_data.yfinance_provider import (
    SYMBOL_REGEX,
    YFinanceProvider,
    clear_cache,
)
from mcp_india_stack.tools.stock_market import (
    get_stock_history,
    get_stock_quote,
    set_market_provider,
)


@pytest.fixture(autouse=True)
def reset_provider_and_cache() -> None:
    """Ensure clean provider state and empty cache before and after each test."""
    clear_cache()
    provider = YFinanceProvider(cache_ttl=60.0, timeout=1.0, retries=1)
    set_market_provider(provider)
    yield
    clear_cache()
    set_market_provider(YFinanceProvider())


def test_malformed_symbol_allowlist_regex() -> None:
    """Symbols violating allowlist regex are rejected before network calls."""
    malformed_symbols = [
        "RELIANCE; DROP TABLE;",
        "<script>alert(1)</script>",
        "!@#$%^&*()",
        "A" * 25,  # Exceeds 20 chars
        " INVALID.NS",
        "INVALID.NS ",
    ]

    for sym in malformed_symbols:
        res = get_stock_quote(sym)
        assert res["success"] is False
        assert "errors" in res
        assert any("Malformed stock symbol" in err for err in res["errors"])
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True
        assert "as_of" in res

    # Empty symbol check
    res_empty = get_stock_quote("")
    assert res_empty["success"] is False
    assert "Stock symbol is required" in res_empty["errors"][0]


def test_valid_symbol_regex_patterns() -> None:
    """Valid Indian ticker formats pass allowlist regex."""
    valid_symbols = [
        "RELIANCE.NS",
        "TCS.BO",
        "INFY",
        "^NSEI",
        "^BSESN",
        "NIFTY_50.NS",
        "M&M.NS".replace("&", "_"),  # Alphanumeric with underscore
        "HDFC-BANK.NS",
    ]
    for sym in valid_symbols:
        assert SYMBOL_REGEX.match(sym) is not None


def test_empty_historical_frame() -> None:
    """Empty dataframe from yfinance returns structured error and no crash."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = get_stock_history("RELIANCE.NS", period="1mo")
        assert res["success"] is False
        assert any("No historical data found" in err for err in res["errors"])
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True
        assert "as_of" in res


def test_delisted_or_missing_symbol() -> None:
    """Delisted or non-existent ticker with empty info returns structured error."""
    mock_ticker = MagicMock()
    # Empty info dict
    mock_ticker.info = {}

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = get_stock_quote("DELISTED.NS")
        assert res["success"] is False
        assert any("delisted or invalid" in err for err in res["errors"])
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True
        assert "as_of" in res

    # Info with only name but no prices
    mock_ticker.info = {"shortName": "Dead Entity"}
    clear_cache()
    with patch("yfinance.Ticker", return_value=mock_ticker):
        res2 = get_stock_quote("DEAD.BO")
        assert res2["success"] is False
        assert any("delisted or invalid" in err for err in res2["errors"])


def test_timeout_and_backoff_handling() -> None:
    """Timeout during fetch is caught, retried, and returns structured error."""
    mock_ticker = MagicMock()

    def _timeout_info() -> dict[str, str]:
        raise TimeoutError("Upstream socket timed out")

    type(mock_ticker).info = property(lambda self: _timeout_info())

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = get_stock_quote("TIMEOUT.NS")
        assert res["success"] is False
        assert any("timed out" in err.lower() for err in res["errors"])
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True


def test_partial_data_handling() -> None:
    """Partial info with missing metadata does not crash and populates available data."""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "symbol": "PARTIAL.NS",
        "currentPrice": 450.25,
        "regularMarketPrice": 450.25,
        "shortName": "Partial Ticker Ltd",
        # All other fields (marketCap, volume, open, dayHigh) omitted/None
    }

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = get_stock_quote("PARTIAL.NS")
        assert res["success"] is True
        assert res["symbol"] == "PARTIAL.NS"
        assert res["currentPrice"] == 450.25
        assert res["shortName"] == "Partial Ticker Ltd"
        assert res["marketCap"] is None
        assert res["volume"] is None
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True
        assert "as_of" in res


def test_rate_limited_upstream() -> None:
    """Upstream 429 Too Many Requests is mapped to structured error."""
    mock_ticker = MagicMock()

    def _rate_limited_call() -> None:
        raise RuntimeError("HTTP Error 429: Too Many Requests")

    type(mock_ticker).info = property(lambda self: _rate_limited_call())

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = get_stock_quote("RATELIMIT.NS")
        assert res["success"] is False
        assert any("rate limit exceeded" in err.lower() for err in res["errors"])
        assert res["data_source"] == "yfinance (unofficial)"
        assert res["delayed"] is True
        assert res["experimental"] is True


def test_short_ttl_cache_deduplication() -> None:
    """Consecutive calls within TTL return cached data without invoking provider."""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "symbol": "CACHED.NS",
        "currentPrice": 1200.0,
        "regularMarketPrice": 1200.0,
        "shortName": "Cached Corp",
    }

    with patch("yfinance.Ticker", return_value=mock_ticker) as mock_yf:
        # First call: hits provider
        res1 = get_stock_quote("CACHED.NS")
        assert res1["success"] is True
        assert res1["currentPrice"] == 1200.0
        assert mock_yf.call_count == 1

        # Second call: served from cache
        res2 = get_stock_quote("CACHED.NS")
        assert res2["success"] is True
        assert res2["currentPrice"] == 1200.0
        assert mock_yf.call_count == 1

        # Clear cache and call again: hits provider
        clear_cache()
        res3 = get_stock_quote("CACHED.NS")
        assert res3["success"] is True
        assert mock_yf.call_count == 2


def test_experimental_marking_in_registrations() -> None:
    """Both registered tools are explicitly marked as [Experimental]."""
    assert reg_get_stock_quote.__doc__ is not None
    assert "[Experimental]" in reg_get_stock_quote.__doc__

    assert reg_get_stock_history.__doc__ is not None
    assert "[Experimental]" in reg_get_stock_history.__doc__
