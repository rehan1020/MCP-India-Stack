"""Stock market data tools."""

from __future__ import annotations

from typing import Any

from mcp_india_stack.tools.market_data.provider import MarketDataProvider
from mcp_india_stack.tools.market_data.yfinance_provider import YFinanceProvider
from mcp_india_stack.utils.responses import build_response


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


# Singleton provider instance for the tools to use
_provider: MarketDataProvider = YFinanceProvider()


def set_market_provider(provider: MarketDataProvider) -> None:
    """Override the default market data provider (useful for testing)."""
    global _provider
    _provider = provider


def get_stock_quote(symbol: str) -> dict[str, Any]:
    """Fetch current (delayed) price and summary for a given ticker."""
    try:
        return _provider.get_quote(symbol)
    except Exception as e:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=[f"market data provider unavailable: {str(e)}"],
                source="market_data",
            )
        )


def get_stock_history(symbol: str, period: str = "1mo") -> dict[str, Any]:
    """Fetch historical end-of-day data for a given ticker."""
    try:
        return _provider.get_history(symbol, period)
    except Exception as e:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=[f"market data provider unavailable: {str(e)}"],
                source="market_data",
            )
        )
