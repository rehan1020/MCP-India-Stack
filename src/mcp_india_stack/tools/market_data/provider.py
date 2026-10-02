"""Market data provider interface."""

from __future__ import annotations

from typing import Any, Protocol


class MarketDataProvider(Protocol):
    """Abstract interface for fetching market data.

    Any provider implementing this protocol must return the normalized data shape
    expected by the stock market tools.
    """

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch current (delayed) price and summary for a given ticker.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            A dictionary containing the normalized quote data or an error response.
        """
        ...

    def get_history(self, symbol: str, period: str = "1mo") -> dict[str, Any]:
        """Fetch historical end-of-day data for a given ticker.

        Args:
            symbol: The stock ticker symbol.
            period: The time period to fetch history for (e.g., "1mo", "1y").

        Returns:
            A dictionary containing the normalized history data or an error response.
        """
        ...
