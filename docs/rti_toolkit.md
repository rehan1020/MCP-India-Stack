# RTI Toolkit

> ⚠️ **Legal Disclaimer**: Nothing produced by these tools constitutes legal advice. Outputs are algorithmic estimates based on publicly available statutory text. Consult a qualified advocate before relying on any output. See [LEGAL_NOTICE.md](../LEGAL_NOTICE.md) for full terms.

## calculate_rti_fee

Calculate RTI application fee (central or state-specific, BPL exemption).

**Input:**
- `jurisdiction` (str): 'central' or state name/code.
- `is_bpl` (bool): True if the applicant is Below Poverty Line.

**Output:** `jurisdiction`, `is_bpl`, `application_fee`, `first_page_fee`, `additional_page_fee`, `errors`, `warnings`

**Example prompt:** "Calculate RTI fee for central government if BPL"

**Limitations:** Does not constitute legal advice.


---

## calculate_rti_deadline

Calculate response due date, first appeal deadline, second appeal deadline.

**Input:**
- `application_date` (str): Date of application (YYYY-MM-DD).
- `life_and_liberty` (bool): True if concerns life and liberty (48 hours).

**Output:** `application_date`, `response_deadline`, `first_appeal_deadline`, `second_appeal_deadline`, `errors`, `warnings`

**Example prompt:** "Calculate RTI deadlines for an application filed on Jan 1, 2024"

**Limitations:** Does not account for public holidays.


---

## calculate_rti_penalty_estimate

Estimate penalty for delayed RTI response (₹250/day, capped ₹25,000).

**Input:**
- `due_date` (str): Date the response was due (YYYY-MM-DD).
- `response_date` (str): Date the response was received, or null if pending.

**Output:** `due_date`, `response_date`, `days_delayed`, `penalty_estimate`, `errors`, `warnings`

**Example prompt:** "Estimate RTI penalty if due date was Jan 1 and response received Jan 15"

**Limitations:** Only IC can levy penalties.


---

## draft_rti_application

Generate a template RTI application under Section 6.

**Input:**
- `pio_designation` (str): Designation of the PIO.
- `department` (str): Department name.
- `subject` (str): Subject of the application.
- `questions` (list[str]): List of information sought.
- `applicant_name` (str): Name of applicant.

**Output:** `draft_text`, `errors`, `warnings`

**Example prompt:** "Draft an RTI application for road repair details from PWD"

**Limitations:** Drafts are templates and need review.


---

## draft_first_appeal

Generate a first appeal template under Section 19(1).

**Input:**
- `appellate_authority` (str): Designation of First Appellate Authority.
- `department` (str): Department name.
- `original_rti_date` (str): Date of original application.
- `grounds_for_appeal` (str): Why the appeal is filed (e.g., no response, incomplete info).
- `applicant_name` (str): Name of applicant.

**Output:** `draft_text`, `errors`, `warnings`

**Example prompt:** "Draft a first appeal for an RTI filed on Jan 1 with no response"

**Limitations:** Drafts are templates and need review.


---

## draft_second_appeal

Generate a second appeal template under Section 19(3) to Information Commission.

**Input:**
- `commission_name` (str): Name of Information Commission (e.g., CIC, SIC Maharashtra).
- `first_appeal_date` (str): Date of first appeal.
- `faa_order_date` (str): Date of FAA order (optional).
- `grounds_for_appeal` (str): Why the second appeal is filed.
- `applicant_name` (str): Name of applicant.

**Output:** `draft_text`, `errors`, `warnings`

**Example prompt:** "Draft a second appeal to CIC"

**Limitations:** Drafts are templates and need review.


---
