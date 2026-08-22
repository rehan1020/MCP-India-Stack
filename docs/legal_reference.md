# Legal Reference

> ⚠️ **Legal Disclaimer**: Nothing produced by these tools constitutes legal advice. Outputs are algorithmic estimates based on publicly available statutory text. Consult a qualified advocate before relying on any output. See [LEGAL_NOTICE.md](../LEGAL_NOTICE.md) for full terms.

## decode_cnr_number

Decode and validate a 16-character Case Number Record (CNR) from Indian eCourts.

**Input:**
- `cnr_number` (str): 16-character CNR number.

**Output:** `cnr_number`, `state_code`, `district_code`, `establishment_code`, `case_type`, `year`, `is_valid`, `errors`, `warnings`

**Example prompt:** "Decode the CNR number MHBO010000012024"

**Limitations:** Does not verify if the case is active or exists on the eCourts platform.


---

## lookup_court_establishment_code

Look up court details from a 4-character establishment code.

**Input:**
- `establishment_code` (str): 4-character establishment code.

**Output:** `establishment_code`, `court_name`, `district`, `state`, `errors`, `warnings`

**Example prompt:** "What court has the establishment code BO01?"

**Limitations:** Based on static reference data.


---

## lookup_ipc_section

Look up an IPC section with title, summary, punishment, cognizability, bailability, and BNS crosswalk.

**Input:**
- `section` (str): IPC section number.

**Output:** `section`, `title`, `summary`, `punishment`, `cognizability`, `bailability`, `bns_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup IPC section 420"

**Limitations:** Does not constitute legal advice.


---

## lookup_bns_section

Look up a BNS section with IPC crosswalk.

**Input:**
- `section` (str): BNS section number.

**Output:** `section`, `title`, `summary`, `punishment`, `cognizability`, `bailability`, `ipc_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup BNS section 316"

**Limitations:** Does not constitute legal advice.


---

## lookup_crpc_section

Look up a CrPC section with BNSS crosswalk.

**Input:**
- `section` (str): CrPC section number.

**Output:** `section`, `title`, `summary`, `bnss_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup CrPC section 144"

**Limitations:** Does not constitute legal advice.


---

## lookup_bnss_section

Look up a BNSS section with CrPC crosswalk.

**Input:**
- `section` (str): BNSS section number.

**Output:** `section`, `title`, `summary`, `crpc_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup BNSS section 163"

**Limitations:** Does not constitute legal advice.


---

## lookup_evidence_act_section

Look up an Indian Evidence Act section.

**Input:**
- `section` (str): IEA section number.

**Output:** `section`, `title`, `summary`, `bsa_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup IEA section 100"

**Limitations:** Does not constitute legal advice.


---

## lookup_bsa_section

Look up a BSA section with IEA crosswalk.

**Input:**
- `section` (str): BSA section number.

**Output:** `section`, `title`, `summary`, `iea_crosswalk`, `errors`, `warnings`

**Example prompt:** "Lookup BSA section 103"

**Limitations:** Does not constitute legal advice.


---

## decode_ipc_bns_crosswalk

Bidirectional IPC↔BNS (and CrPC↔BNSS, IEA↔BSA) section mapping.

**Input:**
- `act` (str): The act to map from (e.g., IPC, BNS, CrPC).
- `section` (str): Section number to look up.

**Output:** `act`, `section`, `mapped_act`, `mapped_section`, `errors`, `warnings`

**Example prompt:** "What is the BNS section for IPC 302?"

**Limitations:** Mapping is based on bare acts.


---

## calculate_limitation_deadline

Calculate the limitation deadline for a suit using the Limitation Act 1963.

**Input:**
- `suit_type` (str): Type of suit or application.
- `cause_of_action_date` (str): Date the cause of action arose (YYYY-MM-DD).

**Output:** `suit_type`, `cause_of_action_date`, `limitation_period`, `deadline_date`, `errors`, `warnings`

**Example prompt:** "Calculate limitation deadline for a money recovery suit from Jan 1, 2024"

**Limitations:** This is an algorithmic estimate based on the Limitation Act.


---

## calculate_court_fee

Calculate court fee based on state-specific slab tables.

**Input:**
- `state` (str): State for filing.
- `claim_amount` (float): Value of the claim or suit.

**Output:** `state`, `claim_amount`, `court_fee`, `errors`, `warnings`

**Example prompt:** "Calculate court fee in Maharashtra for a 50 lakh claim"

**Limitations:** Estimates based on static state schedules.


---

## calculate_stamp_duty

Calculate stamp duty and registration fee based on state-specific rates.

**Input:**
- `state` (str): State where property is located.
- `property_value` (float): Value of the property.
- `gender` (str): Gender of the buyer (optional, some states have rebates).

**Output:** `state`, `property_value`, `gender`, `stamp_duty`, `registration_fee`, `total_fee`, `errors`, `warnings`

**Example prompt:** "Calculate stamp duty in Karnataka for a 1 crore property for a female buyer"

**Limitations:** Estimates based on static state schedules.


---
