# calculate_capital_gains

Calculates capital gains tax for equity, mutual funds, real estate, gold, debentures, and crypto.

**Input:** `sale_price` (float), `purchase_price` (float), `asset_type` (str), `holding_period_days` (int), `inflation_index_purchase` (float | null), `inflation_index_sale` (float | null), `expenses_on_sale` (float), `improvements` (float).

**Output:** `short_term_gains`, `long_term_gains`, `total_gains`, `is_long_term`, `holding_period_days`, `tax_liability`, `asset_type`, `stcg_rate`, `ltcg_rate`, `cost_inflation_adjusted`, `exemption_threshold`, `errors`, `warnings`.

**Example prompt:** "Calculate capital gains on sale of equity shares held for 500 days"

**Limitations:** Tax treatment varies by asset class and notification date. Use this as an estimate only.
