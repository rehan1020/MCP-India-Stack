# FX Rates (INR)

Three live, zero-auth lookups for the official and bank FX numbers used in Indian invoicing, GST and customs work. Each returns the **latest published value only**, quoted as INR per 1 unit of the foreign currency.

These tools call `https://allratestoday.com/api/open/...` (no key, no account). They share one circuit breaker (5 consecutive failures opens it for 30 seconds), use a 5-second timeout, and never raise: on any failure the response has `success: false` and the reason in `errors`.

> These are the only tools in the package, together with the stock market tools, that need network access.

---

## inr_reference_rate

Latest RBI reference rate for a currency against INR. Use for the rate a regulation, contract or auditor refers to as "the RBI rate".

**Input:**
- `currency` (str): ISO 4217 code. RBI publishes `USD`, `EUR`, `GBP`, `JPY`, `AED`, `IDR`.

**Output:** `currency`, `quote` (`INR`), `value`, `rate_date`, `rate_type` (`reference`), `source` (`rbi_reference_rate`), `source_url`, `errors`, `warnings`.

**Example prompt:** "What is today's RBI reference rate for USD?"

**Limitations:** Latest value only, no history. A currency RBI does not publish returns `success: false` with the list of available codes in `errors`.

---

## sbi_tt_rate

Latest State Bank of India telegraphic-transfer (TT) buy and sell rate for a currency against INR, as shown on SBI's own forex card-rate sheet.

**Input:**
- `currency` (str): ISO 4217 code, e.g. `USD`, `EUR`, `AED`, `SGD`.

**Output:** `currency`, `quote` (`INR`), `buy`, `sell`, `value` (mid of buy/sell), `rate_date` (capture date), `bank_updated_at` (SBI's own timestamp, as printed), `basis`, `rate_type` (`tt`), `source` (`sbi_tt_rate`), `source_url`, `errors`, `warnings`.

**Example prompt:** "What is SBI's TT selling rate for EUR right now?"

**Limitations:** Indicative retail board rate, not an official or reference rate; SBI changes it through the day. Currencies SBI does not display return `success: false`.

---

## cbic_customs_rate

Latest CBIC (Central Board of Indirect Taxes and Customs) notified exchange rate for a currency against INR, for import or export valuation.

**Input:**
- `currency` (str): ISO 4217 code, e.g. `USD`, `EUR`, `CNY`.
- `type` (str): `import` (default) or `export`.

**Output:** `currency`, `quote` (`INR`), `value`, `rate_date` (notification date), `rate_type` (`import` | `export`), `source` (`cbic_customs_rate`), `source_url`, `errors`, `warnings`.

**Example prompt:** "Give me the CBIC customs import rate for USD for this bill of entry."

**Limitations:** CBIC notifies rates roughly fortnightly, so `rate_date` is normally older than today; the tool adds a warning when the source flags the table as stale.
