"""yfinance-based market data provider implementation.

Hardened with:
- Strict symbol allowlist regex
- Short-TTL in-memory cache
- Bounded timeouts with backoff retries
- Exception mapping (no raw exceptions escape)
- Additive metadata: data_source, delayed, as_of, experimental
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from mcp_india_stack.tools.market_data.provider import MarketDataProvider
from mcp_india_stack.utils.responses import build_response

# Indian market symbols: ticker, index (e.g. ^NSEI), NSE (.NS), BSE (.BO)
SYMBOL_REGEX = re.compile(r"^[A-Za-z0-9^][A-Za-z0-9._\-^]{0,19}$")

_DEFAULT_CACHE_TTL: float = 60.0
_DEFAULT_TIMEOUT: float = 5.0
_DEFAULT_RETRIES: int = 2

# Thread-safe in-memory cache: key -> (cached_at_timestamp, result_dict)
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()


def clear_cache() -> None:
    """Clear in-memory market data cache (primarily for tests)."""
    with _CACHE_LOCK:
        _CACHE.clear()


def _get_from_cache(key: str, ttl: float) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None
        cached_time, data = entry
        if time.monotonic() - cached_time < ttl:
            return dict(data)
        _CACHE.pop(key, None)
        return None


def _set_in_cache(key: str, data: dict[str, Any]) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic(), dict(data))


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


def _run_with_timeout_and_retry(
    func: Callable[[], Any],
    timeout_seconds: float = _DEFAULT_TIMEOUT,
    max_retries: int = _DEFAULT_RETRIES,
) -> Any:
    """Execute a callable in a worker thread with timeout and exponential backoff retries."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(func)
            try:
                return future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                last_exc = TimeoutError("Upstream market data request timed out")
            except Exception as e:
                last_exc = e

        if attempt < max_retries:
            time.sleep(0.05 * (2**attempt))

    if last_exc:
        raise last_exc
    raise RuntimeError("Market data fetch failed after retries")


class YFinanceProvider(MarketDataProvider):
    """Implementation of MarketDataProvider using the yfinance library with resilience guards."""

    def __init__(
        self,
        cache_ttl: float | None = None,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> None:
        if cache_ttl is not None:
            self.cache_ttl = cache_ttl
        else:
            try:
                self.cache_ttl = float(
                    os.environ.get("MCP_INDIA_STACK_YFINANCE_CACHE_TTL", _DEFAULT_CACHE_TTL)
                )
            except ValueError:
                self.cache_ttl = _DEFAULT_CACHE_TTL

        if timeout is not None:
            self.timeout = timeout
        else:
            try:
                self.timeout = float(
                    os.environ.get("MCP_INDIA_STACK_YFINANCE_TIMEOUT", _DEFAULT_TIMEOUT)
                )
            except ValueError:
                self.timeout = _DEFAULT_TIMEOUT

        self.retries = retries if retries is not None else _DEFAULT_RETRIES

    def clear_cache(self) -> None:
        """Clear cache for this provider."""
        clear_cache()

    def get_quote(self, symbol: str) -> dict[str, Any]:  # noqa: C901
        """Fetch current (delayed) price and summary for a given ticker."""
        as_of = datetime.now(timezone.utc).isoformat()
        metadata_envelope = {
            "data_source": "yfinance (unofficial)",
            "delayed": True,
            "as_of": as_of,
            "experimental": True,
        }

        if not symbol:
            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=["Stock symbol is required"],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)

        if not SYMBOL_REGEX.match(symbol):
            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=[
                    f"Malformed stock symbol: {symbol!r}. "
                    f"Must match allowlist regex: {SYMBOL_REGEX.pattern}"
                ],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)

        clean_symbol = symbol
        cache_key = f"quote:{clean_symbol.upper()}"
        cached = _get_from_cache(cache_key, self.cache_ttl)
        if cached is not None:
            return cached

        try:
            ticker = yf.Ticker(clean_symbol)
            info = _run_with_timeout_and_retry(
                lambda: ticker.info,
                timeout_seconds=self.timeout,
                max_retries=self.retries,
            )

            has_price = False
            if isinstance(info, dict):
                has_price = any(
                    info.get(k) is not None
                    for k in ("regularMarketPrice", "currentPrice", "previousClose")
                )

            if not info or not has_price:
                res = build_response(
                    success=False,
                    data=dict(metadata_envelope),
                    errors=[
                        f"Could not fetch data for symbol {clean_symbol} (delisted or invalid)"
                    ],
                    source="yfinance",
                )
                res.update(metadata_envelope)
                return _flatten(res)

            data = {
                "symbol": clean_symbol,
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
                **metadata_envelope,
            }

            res = _flatten(
                build_response(
                    success=True,
                    data=data,
                    warnings=["Data may be delayed by up to 15 minutes."],
                    source="yfinance",
                )
            )
            res.update(metadata_envelope)
            _set_in_cache(cache_key, res)
            return res

        except Exception as e:
            err_msg = str(e)
            is_429 = (
                "rate limit" in err_msg.lower()
                or "too many requests" in err_msg.lower()
                or "429" in err_msg
            )
            if is_429:
                mapped_error = f"Rate limit exceeded while fetching quote for {clean_symbol}"
            elif isinstance(e, TimeoutError) or "timed out" in err_msg.lower():
                mapped_error = f"Request timed out fetching quote for {clean_symbol}"
            else:
                mapped_error = f"Error fetching quote for {clean_symbol}: {err_msg}"

            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=[mapped_error],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)

    def get_history(self, symbol: str, period: str = "1mo") -> dict[str, Any]:  # noqa: C901
        """Fetch historical end-of-day data for a given ticker."""
        as_of = datetime.now(timezone.utc).isoformat()
        metadata_envelope = {
            "data_source": "yfinance (unofficial)",
            "delayed": True,
            "as_of": as_of,
            "experimental": True,
        }

        if not symbol:
            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=["Stock symbol is required"],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)

        if not SYMBOL_REGEX.match(symbol):
            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=[
                    f"Malformed stock symbol: {symbol!r}. "
                    f"Must match allowlist regex: {SYMBOL_REGEX.pattern}"
                ],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)

        clean_symbol = symbol
        cache_key = f"history:{clean_symbol.upper()}:{period}"
        cached = _get_from_cache(cache_key, self.cache_ttl)
        if cached is not None:
            return cached

        try:
            ticker = yf.Ticker(clean_symbol)
            hist = _run_with_timeout_and_retry(
                lambda: ticker.history(period=period),
                timeout_seconds=self.timeout,
                max_retries=self.retries,
            )

            if hist is None or getattr(hist, "empty", True):
                res = build_response(
                    success=False,
                    data=dict(metadata_envelope),
                    errors=[
                        f"No historical data found for symbol {clean_symbol} with period {period}"
                    ],
                    source="yfinance",
                )
                res.update(metadata_envelope)
                return _flatten(res)

            # Reset index to make Date a column and convert it to string
            hist = hist.reset_index()
            if "Date" in hist.columns:
                hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")

            records = hist.to_dict(orient="records")

            data = {
                "symbol": clean_symbol,
                "period": period,
                "history": records,
                **metadata_envelope,
            }

            res = _flatten(
                build_response(
                    success=True,
                    data=data,
                    warnings=["Data may be delayed by up to 15 minutes."],
                    source="yfinance",
                )
            )
            res.update(metadata_envelope)
            _set_in_cache(cache_key, res)
            return res

        except Exception as e:
            err_msg = str(e)
            is_429 = (
                "rate limit" in err_msg.lower()
                or "too many requests" in err_msg.lower()
                or "429" in err_msg
            )
            if is_429:
                mapped_error = f"Rate limit exceeded while fetching history for {clean_symbol}"
            elif isinstance(e, TimeoutError) or "timed out" in err_msg.lower():
                mapped_error = f"Request timed out fetching history for {clean_symbol}"
            else:
                mapped_error = f"Error fetching history for {clean_symbol}: {err_msg}"

            res = build_response(
                success=False,
                data=dict(metadata_envelope),
                errors=[mapped_error],
                source="yfinance",
            )
            res.update(metadata_envelope)
            return _flatten(res)
