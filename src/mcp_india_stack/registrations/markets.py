from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
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
