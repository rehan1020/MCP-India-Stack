"""Tests for market data provider abstractions and error handling."""

from typing import Any

from mcp_india_stack.tools.market_data.provider import MarketDataProvider
from mcp_india_stack.tools.stock_market import (
    get_stock_history,
    get_stock_quote,
    set_market_provider,
)


class FakeProvider(MarketDataProvider):
    """A fake provider that returns fixed data."""

    def get_quote(self, symbol: str) -> dict[str, Any]:
        return {
            "success": True,
            "symbol": symbol,
            "currentPrice": 100.5,
            "shortName": f"{symbol} Inc.",
            "warnings": [],
            "source": "fake",
        }

    def get_history(self, symbol: str, period: str = "1mo") -> dict[str, Any]:
        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "history": [{"Date": "2023-01-01", "Close": 100.0}],
            "warnings": [],
            "source": "fake",
        }


class ErrorProvider(MarketDataProvider):
    """A provider that simulates an unhandled crash."""

    def get_quote(self, symbol: str) -> dict[str, Any]:
        raise ValueError("Simulated network or parsing crash")

    def get_history(self, symbol: str, period: str = "1mo") -> dict[str, Any]:
        raise ValueError("Simulated network or parsing crash")


def test_stock_quote_fake_provider() -> None:
    set_market_provider(FakeProvider())
    try:
        res = get_stock_quote("RELIANCE.NS")
        assert res["success"] is True
        assert res["symbol"] == "RELIANCE.NS"
        assert res["currentPrice"] == 100.5
        assert res["source"] == "fake"
    finally:
        from mcp_india_stack.tools.market_data.yfinance_provider import YFinanceProvider

        set_market_provider(YFinanceProvider())


def test_stock_history_fake_provider() -> None:
    set_market_provider(FakeProvider())
    try:
        res = get_stock_history("RELIANCE.NS", "1y")
        assert res["success"] is True
        assert res["symbol"] == "RELIANCE.NS"
        assert res["period"] == "1y"
        assert res["history"][0]["Close"] == 100.0
        assert res["source"] == "fake"
    finally:
        from mcp_india_stack.tools.market_data.yfinance_provider import YFinanceProvider

        set_market_provider(YFinanceProvider())


def test_stock_quote_error_boundary() -> None:
    set_market_provider(ErrorProvider())
    try:
        res = get_stock_quote("RELIANCE.NS")
        assert res["success"] is False
        assert "errors" in res
        assert (
            "market data provider unavailable: Simulated network or parsing crash"
            in res["errors"][0]
        )
    finally:
        from mcp_india_stack.tools.market_data.yfinance_provider import YFinanceProvider

        set_market_provider(YFinanceProvider())


def test_stock_history_error_boundary() -> None:
    set_market_provider(ErrorProvider())
    try:
        res = get_stock_history("RELIANCE.NS", "1y")
        assert res["success"] is False
        assert "errors" in res
        assert (
            "market data provider unavailable: Simulated network or parsing crash"
            in res["errors"][0]
        )
    finally:
        from mcp_india_stack.tools.market_data.yfinance_provider import YFinanceProvider

        set_market_provider(YFinanceProvider())
