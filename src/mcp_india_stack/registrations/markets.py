from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.fx_rates import cbic_customs_rate as core_cbic_customs_rate
from mcp_india_stack.tools.fx_rates import inr_reference_rate as core_inr_reference_rate
from mcp_india_stack.tools.fx_rates import sbi_tt_rate as core_sbi_tt_rate
from mcp_india_stack.tools.stock_market import get_stock_history as core_get_stock_history
from mcp_india_stack.tools.stock_market import get_stock_quote as core_get_stock_quote


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
def get_stock_quote(
    symbol: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="Stock symbol/ticker to fetch. Examples: RELIANCE.NS, INFY.NS, TCS.BO",
        ),
    ],
) -> dict[str, Any]:
    """Fetch current (delayed) price and summary for a given Indian stock ticker."""
    return core_get_stock_quote(symbol=symbol)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
def get_stock_history(
    symbol: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20,
            description="Stock symbol/ticker to fetch. Examples: RELIANCE.NS, INFY.NS",
        ),
    ],
    period: Annotated[
        str,
        Field(
            default="1mo",
            description="Time period to fetch data for. Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max",  # noqa: E501
        ),
    ] = "1mo",
) -> dict[str, Any]:
    """Fetch historical end-of-day data for a given Indian stock ticker."""
    return core_get_stock_history(symbol=symbol, period=period)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
def inr_reference_rate(
    currency: Annotated[
        str,
        Field(
            min_length=3,
            max_length=3,
            description="ISO 4217 currency code quoted against INR. Examples: USD, EUR, GBP, JPY",
        ),
    ],
) -> dict[str, Any]:
    """Fetch the latest RBI reference rate for a currency against INR (zero-auth live lookup)."""
    return core_inr_reference_rate(currency=currency)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
def sbi_tt_rate(
    currency: Annotated[
        str,
        Field(
            min_length=3,
            max_length=3,
            description="ISO 4217 currency code quoted against INR. Examples: USD, EUR, AED",
        ),
    ],
) -> dict[str, Any]:
    """Fetch the latest SBI telegraphic-transfer buy/sell rate for a currency against INR."""
    return core_sbi_tt_rate(currency=currency)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
def cbic_customs_rate(
    currency: Annotated[
        str,
        Field(
            min_length=3,
            max_length=3,
            description="ISO 4217 currency code quoted against INR. Examples: USD, EUR, CNY",
        ),
    ],
    type: Annotated[
        str,
        Field(
            default="import",
            description="Customs rate type: import or export",
        ),
    ] = "import",
) -> dict[str, Any]:
    """Fetch the latest CBIC customs exchange rate (import or export) for a currency against INR."""
    return core_cbic_customs_rate(currency=currency, type=type)
