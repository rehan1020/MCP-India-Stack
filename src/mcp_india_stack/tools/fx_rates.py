"""Zero-auth INR FX rate tools: RBI reference, SBI TT and CBIC customs rates.

All three tools are live lookups (PermissionTier.LOOKUP_LIVE) against the open,
keyless endpoints at allratestoday.com. They return the latest published value
only, share one process-global circuit breaker, and never raise: any failure
(timeout, non-200, malformed body, breaker open) is reported through the
``errors``/``warnings`` lists with ``success`` set to ``False``.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from mcp_india_stack.tools.ifsc import _CB_COOLDOWN_SECONDS, _CB_FAILURE_THRESHOLD, _CircuitBreaker

_FX_BASE_URL = "https://allratestoday.com/api/open"
_FX_TIMEOUT_SECONDS = 5.0

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_CUSTOMS_TYPES = ("import", "export")

_fx_breaker = _CircuitBreaker(_CB_FAILURE_THRESHOLD, _CB_COOLDOWN_SECONDS)


def _normalize_currency(currency: str | None) -> tuple[str, list[str]]:
    """Upper-case and validate a 3-letter ISO 4217 code."""
    value = (currency or "").strip().upper()
    if not value:
        return value, ["currency is required (ISO 4217 code, e.g. USD)"]
    if not _CURRENCY_RE.match(value):
        return value, ["currency must be a 3-letter ISO 4217 code (e.g. USD, EUR, AED)"]
    return value, []


def _error(
    *,
    currency: str,
    source: str,
    errors: list[str],
    warnings: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": False,
        "currency": currency,
        "quote": "INR",
        "value": None,
        "rate_date": None,
        "source": source,
        "errors": errors,
        "warnings": warnings or [],
    }
    result.update(extra)
    return result


def _fetch_json(path: str, params: dict[str, str] | None = None) -> tuple[Any, int, list[str]]:
    """GET ``_FX_BASE_URL + path`` and return ``(payload, status_code, errors)``.

    Returns ``(None, 0, [...])`` when the breaker is open or the request fails.
    A 404 is not counted against the breaker: the upstream uses it for
    "no rate for this currency", which is a valid answer, not an outage.
    """
    if _fx_breaker.is_open:
        return None, 0, ["fx source unavailable: circuit_open"]
    try:
        with httpx.Client(timeout=_FX_TIMEOUT_SECONDS) as client:
            response = client.get(f"{_FX_BASE_URL}{path}", params=params)
    except Exception:
        _fx_breaker.record_failure()
        return None, 0, ["fx source unavailable or timed out"]

    if response.status_code == 404:
        _fx_breaker.record_success()
        try:
            return response.json(), 404, []
        except ValueError:
            return None, 404, ["fx source returned 404"]

    if response.status_code != 200:
        _fx_breaker.record_failure()
        return None, response.status_code, [f"fx source returned {response.status_code}"]

    try:
        payload = response.json()
    except ValueError:
        _fx_breaker.record_failure()
        return None, 200, ["fx source returned a non-JSON body"]

    _fx_breaker.record_success()
    return payload, 200, []


def _pick_rate(
    payload: Any, currency: str, rate_type: str
) -> tuple[dict[str, Any] | None, list[str]]:
    """Find the ``rates[]`` entry for ``currency``/``rate_type`` in a central-bank table."""
    if not isinstance(payload, dict) or not isinstance(payload.get("rates"), list):
        return None, ["fx source returned an unexpected shape"]
    available: set[str] = set()
    for row in payload["rates"]:
        if not isinstance(row, dict) or row.get("type") != rate_type:
            continue
        base = row.get("base")
        if isinstance(base, str):
            available.add(base)
        if base == currency and row.get("quote") == "INR":
            return row, []
    return None, [
        f"no {rate_type} rate published for {currency}",
        f"available: {', '.join(sorted(available)) or 'none'}",
    ]


def _table_warnings(payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if payload.get("stale") is True:
        age = payload.get("age_days")
        warnings.append(f"rate table flagged stale by source (age_days={age})")
    return warnings


def _central_bank_rate(*, bank: str, source: str, currency: str, rate_type: str) -> dict[str, Any]:
    """Shared path for RBI and CBIC tables served at ``/central-bank/{bank}``."""
    code, errors = _normalize_currency(currency)
    if errors:
        return _error(currency=code, source=source, errors=errors)

    path = f"/central-bank/{bank}"
    payload, status, errors = _fetch_json(path)
    if errors:
        return _error(currency=code, source=source, errors=errors)
    if status == 404:
        msg = payload.get("error") if isinstance(payload, dict) else None
        return _error(
            currency=code, source=source, errors=[str(msg or "no published table available")]
        )

    row, errors = _pick_rate(payload, code, rate_type)
    if row is None:
        return _error(
            currency=code, source=source, errors=errors, rate_date=payload.get("rate_date")
        )

    return {
        "success": True,
        "currency": code,
        "quote": "INR",
        "value": row.get("value"),
        "rate_date": payload.get("rate_date"),
        "rate_type": rate_type,
        "source": source,
        "source_url": f"{_FX_BASE_URL}{path}",
        "errors": [],
        "warnings": _table_warnings(payload),
    }


def inr_reference_rate(currency: str) -> dict[str, Any]:
    """Latest RBI reference rate for ``currency`` against INR.

    Args:
        currency: ISO 4217 code (USD, EUR, GBP, JPY, AED, IDR are published by RBI).

    Returns:
        Dict with ``currency``, ``quote`` ("INR"), ``value``, ``rate_date``, ``source``.
    """
    return _central_bank_rate(
        bank="rbi", source="rbi_reference_rate", currency=currency, rate_type="reference"
    )


def cbic_customs_rate(currency: str, type: str = "import") -> dict[str, Any]:
    """Latest CBIC customs exchange rate for ``currency`` against INR.

    Args:
        currency: ISO 4217 code (e.g. USD).
        type: ``"import"`` or ``"export"`` rate (CBIC notifies both).

    Returns:
        Dict with ``currency``, ``quote`` ("INR"), ``value``, ``rate_date``, ``rate_type``,
        ``source``.
    """
    rate_type = (type or "").strip().lower()
    if rate_type not in _CUSTOMS_TYPES:
        code, _ = _normalize_currency(currency)
        return _error(
            currency=code,
            source="cbic_customs_rate",
            errors=["type must be 'import' or 'export'"],
        )
    return _central_bank_rate(
        bank="cbic", source="cbic_customs_rate", currency=currency, rate_type=rate_type
    )


def sbi_tt_rate(currency: str) -> dict[str, Any]:
    """Latest State Bank of India telegraphic-transfer (TT) buy/sell rate against INR.

    Args:
        currency: ISO 4217 code (e.g. USD).

    Returns:
        Dict with ``currency``, ``quote`` ("INR"), ``buy``, ``sell``, ``value`` (mid),
        ``rate_date``, ``source``. These are indicative board rates, not official rates.
    """
    source = "sbi_tt_rate"
    code, errors = _normalize_currency(currency)
    if errors:
        return _error(currency=code, source=source, errors=errors)

    path = "/bank-rates/in/sbi"
    payload, status, errors = _fetch_json(path, params={"ccy": code})
    if errors:
        return _error(currency=code, source=source, errors=errors)
    if status == 404:
        msg = payload.get("error") if isinstance(payload, dict) else None
        return _error(currency=code, source=source, errors=[str(msg or f"no rate for {code}")])
    if not isinstance(payload, dict) or payload.get("buy") is None or payload.get("sell") is None:
        return _error(
            currency=code, source=source, errors=["fx source returned an unexpected shape"]
        )

    captured_at = payload.get("captured_at")
    rate_date = (
        captured_at[:10] if isinstance(captured_at, str) and len(captured_at) >= 10 else None
    )
    return {
        "success": True,
        "currency": code,
        "quote": "INR",
        "buy": payload.get("buy"),
        "sell": payload.get("sell"),
        "value": payload.get("mid"),
        "rate_date": rate_date,
        "bank_updated_at": payload.get("bank_updated_at"),
        "basis": payload.get("basis"),
        "rate_type": "tt",
        "source": source,
        "source_url": f"{_FX_BASE_URL}{path}?ccy={code}",
        "errors": [],
        "warnings": ["indicative bank board rate, not an official or reference rate"],
    }
