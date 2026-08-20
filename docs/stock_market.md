# Stock Market

## get_stock_quote

Fetch current (delayed) price and summary for a given Indian stock ticker (NSE/BSE). Use when querying live performance, market capitalization, or day high/low for equities.

**Input:**
- `symbol` (str): Stock symbol/ticker to fetch. Examples: `RELIANCE.NS`, `INFY.NS`, `TCS.BO`.

**Output:** `symbol`, `shortName`, `longName`, `currentPrice`, `previousClose`, `open`, `dayLow`, `dayHigh`, `volume`, `marketCap`, `currency`, `exchange`.

**Example prompt:** "Check the current stock price and market cap for Tata Motors (TATAMOTORS.NS)."

**Limitations:** Uses Yahoo Finance as the data source. Market data is generally delayed by up to 15 minutes. Not suitable for high-frequency or real-time trading applications.

---

## get_stock_history

Fetch historical end-of-day data for a given Indian stock ticker for a specified period. Use when querying historical trends, price changes over time, or calculating returns over a period.

**Input:**
- `symbol` (str): Stock symbol/ticker to fetch. Examples: `RELIANCE.NS`, `INFY.NS`.
- `period` (str): Time period to fetch data for. Valid periods: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`. (Default: `1mo`).

**Output:** `symbol`, `period`, `history` (list of dictionaries containing `Date`, `Open`, `High`, `Low`, `Close`, `Volume`).

**Example prompt:** "Pull the 5-day historical stock data for Infosys (INFY.NS)."

**Limitations:** Historical data is end-of-day. Uses Yahoo Finance, subject to fair-use rate limiting.
