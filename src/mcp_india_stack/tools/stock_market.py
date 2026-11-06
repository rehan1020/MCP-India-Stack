"""Stock market data tools."""

from __future__ import annotations

from datetime import datetime, timezone
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
        as_of = datetime.now(timezone.utc).isoformat()
        metadata_envelope = {
            "data_source": "yfinance (unofficial)",
            "delayed": True,
            "as_of": as_of,
            "experimental": True,
        }
        res = build_response(
            success=False,
            data=dict(metadata_envelope),
            errors=[f"market data provider unavailable: {str(e)}"],
            source="market_data",
        )
        res.update(metadata_envelope)
        return _flatten(res)


def get_stock_history(symbol: str, period: str = "1mo") -> dict[str, Any]:
    """Fetch historical end-of-day data for a given ticker."""
    try:
        return _provider.get_history(symbol, period)
    except Exception as e:
        as_of = datetime.now(timezone.utc).isoformat()
        metadata_envelope = {
            "data_source": "yfinance (unofficial)",
            "delayed": True,
            "as_of": as_of,
            "experimental": True,
        }
        res = build_response(
            success=False,
            data=dict(metadata_envelope),
            errors=[f"market data provider unavailable: {str(e)}"],
            source="market_data",
        )
        res.update(metadata_envelope)
        return _flatten(res)
