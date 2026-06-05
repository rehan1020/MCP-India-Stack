# Lookup and Validation Tools

## IFSC Tools

## lookup_ifsc

Validates IFSC format and returns bank branch metadata from bundled dataset with optional live fallback to Razorpay IFSC API.

**Input:** `ifsc_code` (str) — 11-character IFSC code. Case-insensitive. Example: `HDFC0000001`.

**Output:** `found`, `ifsc`, `bank`, `branch`, `address`, `city`, `district`, `state`, `contact`, `upi` (bool), `rtgs` (bool), `neft` (bool), `imps` (bool), `source`.

**Example prompt:** "Get branch details for IFSC ICIC0000001"

**Limitations:** Bundled data may be slightly behind newest branch openings. Live fallback requires internet connectivity.

---

## bulk_validate_ifsc

Validate multiple IFSC codes in parallel. Maximum 500 IFSCs per call.

**Input:** `ifscs` (list[str]) — List of IFSC codes to validate.

**Output:** `results` (list of single lookup outputs), `total`, `found_count`.

**Example prompt:** "Bulk lookup these IFSC codes: HDFC0000001, ICIC0000002"


---

## lookup_pincode

Returns all post offices for a pincode with district, state context and mapped GST state code.

**Input:** `pincode` (str) — 6-digit Indian pincode. Spaces/hyphens accepted.

**Output:** `found`, `pincode`, `state`, `state_code`, `district`, `region`, `post_offices` (list of branch names), `count`.

**Example prompt:** "Which post offices fall under pincode 110001?"

**Limitations:** Pincode boundaries can occasionally change. Geocoding is approximate based on centroid of the postal area.



---

## lookup_hsn_code

Supports exact HSN/SAC lookup and keyword search over descriptions. Returns GST rates and classification metadata.

**Inputs:**
- `code` (str, optional) — Exact 2, 4, 6, or 8 digit HSN/SAC code.
- `keyword` (str, optional) — Token to search within descriptions (e.g., "chocolate").

**Output:** `found`, `matches` (list), `query_type`, `count`, `disclaimer`. 
Each match includes `hsn_code`, `description`, `igst`, `cgst`, `sgst`, `compensation_cess`.

**Example prompt:** "Find the GST rate for HSN code 6109" or "Search HSN for 'solar panels'"

**Limitations:** Rates are for general reference and may be subject to specific notifications or conditions. Always verify with official GST Council notifications.



---

## decode_state_code

Decodes GST state code metadata from a 2-digit code or GSTIN prefix. Provides canonical state name, abbreviation, capital, and GST zone mapping.

**Input:** `value` (str) — Two-digit code (e.g., `27`) or full GSTIN (e.g., `27AAPFU0939F1ZV`).

**Output:** `found`, `state_code`, `state_name`, `abbreviation`, `capital`, `zone`, `is_ut` (boolean), `notes`.

**Example prompt:** "Decode GST state code 27"

**Limitations:** Static mapping of 37+ states and UTs. Does not verify if a particular GSTIN is currently active.



---

## lookup_bbps_biller

Looks up BBPS biller entries from the bundled offline biller directory.

**Input:** `category` (str | null), `state` (str | null), `biller_id` (str | null).

**Output:** `found`, `billers`, `count`, plus matching biller metadata and supported parameters.

**Example prompt:** "Find BBPS electricity billers in Maharashtra"

**Limitations:** Offline biller directory only. For the live NPCI directory, use the official BBPS systems.


---

## lookup_bank

Looks up bank details from the bundled bank master sample by bank name or IFSC prefix.

**Input:** `name_or_code` (str) — bank name or IFSC code prefix.

**Output:** `banks`, `count`.

**Example prompt:** "Look up the bank for IFSC HDFC0000001"

**Limitations:** This is a lightweight bundled lookup. Use `lookup_ifsc` for full branch metadata.


---

## GSTIN Tools

## validate_gstin

Validates GSTIN structure and checksum, decodes state/PAN/entity metadata, and reports category limitations for special classes. Validates structure and checksum only; does not verify active GSTN registration status.

**Input:** `gstin` (str) — 15-character GSTIN. Example: `27AAPFU0939F1ZV`.

**Output:** `valid`, `gstin`, `state_code`, `state_name`, `pan`, `entity_number`, `checksum_digit`, `checksum_valid`, `category`, `errors`, `warnings`.

**Example prompt:** "Validate GSTIN 27AAPFU0939F1ZV"

**Limitations:** Validates format and checksum only. Cannot verify if the GSTIN is currently active or cancelled on the GST portal.

---

## bulk_validate_gstin

Validate multiple GSTINs in parallel using a thread pool. Maximum 500 GSTINs per call.

**Input:** `gstins` (list[str]) — List of GSTIN strings to validate.

**Output:** `results` (list of single validation outputs), `total`, `valid_count`, `invalid_count`.

**Example prompt:** "Validate these GSTINs in bulk: 27AAPFU0939F1ZV, 27AAPFU0939F1ZW"


---

## PAN Tools

## validate_pan

Validates Indian PAN format and decodes entity type from the 4th character. Structural validation only.

**Input:** `pan` (str) — 10-character PAN string. Example: `AAAPL1234C`.

**Output:** `valid`, `pan`, `entity_type_code`, `entity_type`, `pan_type`, `is_individual`, `serial_number`, `check_digit`, `errors`.

**Example prompt:** "Validate PAN AAAPL1234C"

**Limitations:** PAN check character (10th digit) is not publicly algorithmic. This tool validates the 4th character entity type and overall digit/letter structure. Cannot verify if the PAN is valid with IT Department.

---

## bulk_validate_pan

Validate multiple PANs in parallel. Maximum 500 PANs per call.

**Input:** `pans` (list[str]) — List of 10-character PAN strings.

**Output:** `results` (list of single validation outputs), `total`, `valid_count`.

**Example prompt:** "Bulk validate these PANs: AAAPL1234C, BBBCM5678D"

---

## decode_pan_type

Decodes the PAN entity type from the 4th character and provides KYC routing hints.

**Input:** `pan` (str) — 10-character PAN.

**Output:** `pan`, `entity_type_code`, `entity_type_label`, `kyc_routing_hint`.

**Example prompt:** "What is the entity type for PAN AAAPL1234C?"


---

## validate_upi_vpa

Validates UPI VPA structure and decodes known provider handles from curated data.

**Input:** `vpa` (str) — UPI virtual payment address. Example: `user@okaxis`.

**Output:** `valid`, `vpa`, `username`, `handle`, `known_provider`, `provider_name`, `bank_name`, `errors`.

**Example prompt:** "Check if user@okaxis is a valid UPI ID"

**Limitations:** Structural validation only. Does not verify if the specific VPA is registered or active on the NPCI network. Unknown handles are not auto-invalidated.



---

## validate_aadhaar

Validates a 12-digit Indian Aadhaar number using the Verhoeff checksum algorithm. Strips spaces and hyphens, checks first digit (cannot be 0 or 1), and verifies checksum. Format validation only — not connected to UIDAI.

**Input:** `aadhaar` (str) — 12-digit Aadhaar number. Spaces/hyphens accepted.

**Output:** `valid`, `aadhaar`, `formatted` (XXXX XXXX XXXX), `checksum_valid`, `first_digit_valid`, `errors`, `disclaimer`.

**Example prompt:** "Validate this Aadhaar number: 2959 4583 7261"

**Limitations:** Cannot verify identity or active status with UIDAI. Structural and checksum validation only.

---

## bulk_validate_aadhaar

Validate multiple Aadhaar numbers in parallel. Maximum 500 Aadhaars per call.

**Input:** `numbers` (list[str]) — List of Aadhaar numbers.

**Output:** `results` (list of single validation outputs).

**Example prompt:** "Bulk validate these Aadhaar numbers: 295945837261, 999999999999"


---

## validate_voter_id

Validates an Indian Voter ID (EPIC) number format. Standard format: 3 uppercase letters + 7 digits (10 characters). Detects possible legacy EPIC formats issued before 2017 ERONET standardisation.

**Input:** `voter_id` (str) — 10-character EPIC number.

**Output:** `valid`, `epic`, `prefix`, `serial`, `format` (standard/legacy_possible), `errors`, `disclaimer`.

**Example prompt:** "Validate voter ID ABC1234567"

**Limitations:** Format validation only. Cannot verify voter registration status with Election Commission.


---

## validate_driving_license

Validates an Indian driving license number format and decodes state code, RTO code, year of issue, and serial number. Standard post-Sarathi format: 2-letter state + 2-digit RTO + 4-digit year + 7-digit serial (15 chars). Handles non-standard/pre-Sarathi formats gracefully.

**Input:** `dl_number` (str) — DL number, 15 chars standard.

**Output:** `valid`, `dl_number`, `state_code`, `state_name`, `rto_code`, `year_of_issue`, `serial`, `errors`, `disclaimer`.

**Example prompt:** "Validate DL number MH0220191234567"

**Limitations:** Format validation only. Cannot verify license validity or status with transport authority.


---

## validate_passport

Validates an Indian passport number format. Format: 1 uppercase letter (series) + 7 digits = 8 characters. No publicly available checksum.

**Input:** `passport_number` (str) — 8-character passport number.

**Output:** `valid`, `passport_number`, `series_letter`, `serial`, `errors`, `disclaimer`.

**Example prompt:** "Is A1234567 a valid Indian passport number?"

**Limitations:** Format validation only. Cannot verify passport validity or status with MEA.


---

## validate_cin

Validates and decodes an Indian CIN (Company Identification Number). 21 characters: listing status (L/U) + 5-digit NIC code + 2-letter state + 4-digit year + 3-letter company type + 6-digit serial.

**Input:** `cin` (str) — 21-character CIN.

**Output:** `valid`, `cin`, `listing_status`, `nic_code`, `state_code`, `state_name`, `year_of_incorporation`, `company_type_code`, `company_type`, `sequential_number`, `errors`.

**Example prompt:** "Decode CIN L17110MH1973PLC019786"

**Limitations:** Format validation with field decoding. No public checksum algorithm. Cannot verify company registration status with MCA.


---

## validate_din

Validates an Indian DIN (Director Identification Number). Exactly 8 digits. Zero-pads shorter input.

**Input:** `din` (str) — 8-digit DIN.

**Output:** `valid`, `din` (normalized), `errors`, `disclaimer`.

**Example prompt:** "Validate DIN 00012345"

**Limitations:** Format validation only. Cannot verify director status with MCA.


---

## validate_fssai

Validates a 14-digit FSSAI license number and decodes the embedded state, year, and license type.

**Input:** `license_number` (str) — 14-digit FSSAI license number. Spaces and dashes are ignored.

**Output:** `valid`, `license_number`, `normalized_input`, `state_code`, `state_name`, `license_year`, `license_type_code`, `license_type`, `sequence_number`, `errors`, `warnings`.

**Example prompt:** "Validate FSSAI license number 10019000000001"

**Limitations:** Format validation and decoding only. It does not verify whether the license is currently active on the FSSAI portal.


---

## validate_epf_code

Validates an EPF establishment code in the `XX/XXXXX/XXXXXX/XXX` format.

**Input:** `code` (str) — EPF establishment code.

**Output:** `valid`, `normalized_input`, `region_code`, `office_code`, `establishment_code`, `extension`, `errors`, `warnings`.

**Example prompt:** "Validate EPF code 07/12345/678901/001"

**Limitations:** Format validation only. It does not query EPFO registration status.


---

## validate_esic_code

Validates an ESIC employer code in the `XX-XXXXX-XXXXX` format.

**Input:** `code` (str) — ESIC employer code.

**Output:** `valid`, `normalized_input`, `regional_code`, `employer_code`, `sub_code`, `errors`, `warnings`.

**Example prompt:** "Validate ESIC code 13-12345-67890"

**Limitations:** Format validation only. It does not check ESIC portal registration.


---

## validate_tan

Validate TAN (Tax Deduction Account Number) format. Use when verifying TAN format for TDS compliance.

**Input:**
- `tan` (str): 10-character TAN (e.g., ABCD12345E).

**Output:** `valid`, `tan`, `error` (if invalid).

**Example prompt:** "Validate TAN ABCD12345E"

**Limitations:** Format validation only. Cannot verify if TAN is active with IT Department.


---

## validate_pran

Validate PRAN (Permanent Retirement Account Number) for NPS. Use when verifying NPS account numbers.

**Input:**
- `pran` (str): 12-digit PRAN.

**Output:** `valid`, `pran`, `subscriber_category`.

**Example prompt:** "Validate PRAN 110012345678"

**Limitations:** Format validation only.


---

## validate_llpin

Validate LLPIN (Limited Liability Partnership Identification Number). Use when verifying LLP registration numbers.

**Input:**
- `llpin` (str): LLPIN in format AAA-XXXX or AAAXXXX.

**Output:** `valid`, `llpin`, `decoded_segments`.

**Example prompt:** "Validate LLPIN AAA-1234"

**Limitations:** Format validation only. Cannot verify active status with MCA.


---

## decode_isin

Decode ISIN (International Securities Identification Number) with Luhn check. Use when validating ISIN for Indian securities.

**Input:**
- `isin` (str): 12-character ISIN (e.g., INE1234567890).

**Output:** `valid`, `isin`, `country`, `nsin`, `security_type`, `luhn_validation`.

**Example prompt:** "Decode ISIN INE1234567890"

**Limitations:** Supports structural and checksum validation only.


---

## decode_digilocker_uri

Decodes a DigiLocker URI and maps it to the best matching validator.

**Input:** `uri` (str) — DigiLocker URI starting with `dlg://`.

**Output:** `uri`, `issuer`, `document_type`, `expected_fields`, `verification_pairing`, `normalized_input`, `errors`, `warnings`.

**Example prompt:** "Decode DigiLocker URI dlg://uidai/aadhaar/123456789012"

**Limitations:** This only parses and maps the URI. It does not verify the document with DigiLocker itself.


---

## validate_mobile_number

Validate Indian mobile number and detect operator/circle. Use when validating mobile numbers for KYC or contact verification.

**Input:**
- `mobile` (str): 10-digit mobile number with or without +91/0.

**Output:** `valid`, `mobile`, `operator`, `telecom_circle`.

**Example prompt:** "Validate mobile number +919876543210"

**Limitations:** Based on TRAI series allocation. Number portability (MNP) is not checked, so actual operator might differ.


---

