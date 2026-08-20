"""Stock market data tools."""

from __future__ import annotations

from typing import Any

import yfinance as yf

from mcp_india_stack.utils.responses import build_response


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


def get_stock_quote(symbol: str) -> dict[str, Any]:
    """Fetch current (delayed) price and summary for a given ticker."""
    if not symbol:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=["Stock symbol is required"],
                source="yfinance",
            )
        )

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        has_price = any(k in info for k in ("regularMarketPrice", "currentPrice", "previousClose"))
        if not info or not has_price:
            return _flatten(
                build_response(
                    success=False,
                    data={},
                    errors=[f"Could not fetch data for symbol {symbol}"],
                    source="yfinance",
                )
            )

        data = {
            "symbol": symbol,
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previousClose": info.get("previousClose"),
            "open": info.get("open"),
            "dayLow": info.get("dayLow"),
            "dayHigh": info.get("dayHigh"),
            "volume": info.get("volume"),
            "marketCap": info.get("marketCap"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
        }

        return _flatten(
            build_response(
                success=True,
                data=data,
                warnings=["Data may be delayed by up to 15 minutes."],
                source="yfinance",
            )
        )
    except Exception as e:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=[f"Error fetching quote for {symbol}: {str(e)}"],
                source="yfinance",
            )
        )


def get_stock_history(symbol: str, period: str = "1mo") -> dict[str, Any]:
    """Fetch historical end-of-day data for a given ticker."""
    if not symbol:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=["Stock symbol is required"],
                source="yfinance",
            )
        )

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return _flatten(
                build_response(
                    success=False,
                    data={},
                    errors=[f"No historical data found for symbol {symbol} with period {period}"],
                    source="yfinance",
                )
            )

        # Reset index to make Date a column and convert it to string
        hist = hist.reset_index()
        hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")

        records = hist.to_dict(orient="records")

        data = {"symbol": symbol, "period": period, "history": records}

        return _flatten(
            build_response(
                success=True,
                data=data,
                warnings=["Data may be delayed by up to 15 minutes."],
                source="yfinance",
            )
        )
    except Exception as e:
        return _flatten(
            build_response(
                success=False,
                data={},
                errors=[f"Error fetching history for {symbol}: {str(e)}"],
                source="yfinance",
            )
        )
