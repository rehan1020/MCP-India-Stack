# FX Rates (INR)

Three live, zero-auth lookups for the FX figures used in Indian invoicing, GST and customs work: the RBI reference rate, the SBI telegraphic-transfer rate and the CBIC customs rate. Each returns the **latest value only**, quoted as INR per 1 unit of the foreign currency.

## Source and provenance

These tools do **not** fetch from RBI, SBI or CBIC. They call `https://allratestoday.com/api/open/...`, a third-party aggregator that collects the figures from those publishers and republishes them (no key, no account). This package does not check the returned values against the authority, so treat them as unverified and confirm with the authority before statutory use.

Every result, including error results, says so in its fields:

- `data_source`: `allratestoday.com (third-party aggregator, unverified)`
- `authority`: the body whose figure the aggregator republishes (`Reserve Bank of India`, `State Bank of India`, `Central Board of Indirect Taxes and Customs`)
- `verified`: always `false`
- `source_url`: the aggregator URL that was called, not an RBI, SBI or CBIC URL
- `as_of`: UTC time of the lookup
- `warnings`: the first entry on a successful result states that the value comes from a third-party aggregator

## Network

Unlike the rest of the package, these tools are not offline-first. Their network tier is `required` (`tools_network` in `india://status`), the same tier as the stock market tools: there is no bundled dataset and no offline fallback. With the network blocked they return `success: false`.

They share one circuit breaker (5 consecutive failures open it for 30 seconds) and use a 5-second timeout. They never raise: on any failure the response has `success: false` and the reason in `errors`. A timeout, a non-200 status other than 404, a non-JSON body and a 200 response with the wrong shape (for example `null`, a list, or a table without a `rates` list) all count as breaker failures. A 404 and a well-formed table that lacks the requested currency are answers, not failures.

---

## inr_reference_rate

Latest RBI reference rate for a currency against INR, as republished by the aggregator.

**Input:**
- `currency` (str): ISO 4217 code. RBI publishes `USD`, `EUR`, `GBP`, `JPY`, `AED`, `IDR`.

**Output:** `currency`, `quote` (`INR`), `value`, `rate_date`, `rate_type` (`reference`), `source` (`rbi_reference_rate`), `source_url`, `data_source`, `authority`, `verified`, `as_of`, `errors`, `warnings`.

**Example prompt:** "What is today's RBI reference rate for USD?"

**Limitations:** Latest value only, no history. A currency RBI does not publish returns `success: false` with the list of available codes in `errors`. A value that is not a positive number is rejected.

---

## sbi_tt_rate

Latest State Bank of India telegraphic-transfer (TT) buy and sell rate for a currency against INR, as the aggregator read it from SBI's forex card-rate sheet.

**Input:**
- `currency` (str): ISO 4217 code, e.g. `USD`, `EUR`, `AED`, `SGD`.

**Output:** `currency`, `quote` (`INR`), `buy`, `sell`, `value` (mid of buy/sell), `rate_date` (date the aggregator captured the sheet), `bank_updated_at` (the timestamp printed on SBI's sheet, as captured), `basis`, `rate_type` (`tt`), `source` (`sbi_tt_rate`), `source_url`, `data_source`, `authority`, `verified`, `as_of`, `errors`, `warnings`.

**Example prompt:** "What is SBI's TT selling rate for EUR right now?"

**Limitations:** Indicative retail board rate, not an official or reference rate; SBI changes it through the day and the aggregator's copy can lag. Currencies SBI does not display return `success: false`.

---

## cbic_customs_rate

Latest CBIC (Central Board of Indirect Taxes and Customs) notified exchange rate for a currency against INR, for import or export valuation, as republished by the aggregator.

**Input:**
- `currency` (str): ISO 4217 code, e.g. `USD`, `EUR`, `CNY`.
- `type` (str): `import` (default) or `export`.

**Output:** `currency`, `quote` (`INR`), `value`, `rate_date` (notification date), `rate_type` (`import` | `export`), `source` (`cbic_customs_rate`), `source_url`, `data_source`, `authority`, `verified`, `as_of`, `errors`, `warnings`.

**Example prompt:** "Give me the CBIC customs import rate for USD for this bill of entry."

**Limitations:** CBIC notifies rates roughly fortnightly, so `rate_date` is normally older than today; the tool adds a warning when the source flags the table as stale. For a bill of entry or shipping bill, check the rate against the CBIC notification itself.
