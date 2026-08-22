from __future__ import annotations

import datetime
import functools
import json
import pathlib
from typing import Any


@functools.lru_cache(maxsize=1)
def _load_rti_fees() -> dict[str, Any]:
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "rti" / "rti_fees.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def calculate_rti_fee(
    state_code: str = "central", applicant_category: str = "general"
) -> dict[str, Any]:
    """
    Calculate the RTI application fee based on state rules.

    Input:
    - state_code (str): 2-letter state code or "central".
    - applicant_category (str): "general" or "bpl".

    Output: application_fee, additional_page_fee, bpl_exempt, state_info, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    if applicant_category.lower() == "bpl":
        return {
            "application_fee": 0,
            "additional_page_fee": 0,
            "bpl_exempt": True,
            "state_info": state_code,
            "errors": errors,
            "warnings": warnings,
        }

    data = _load_rti_fees()
    code = state_code.upper() if state_code.lower() != "central" else "central"
    state_data = data.get(code)

    if not state_data:
        warnings.append(f"RTI fee data not available for {code}, defaulting to central rules.")
        state_data = data.get("central", {"application_fee": 10, "additional_page_fee": 2})

    return {
        "application_fee": state_data.get("application_fee", 10),
        "additional_page_fee": state_data.get("additional_page_fee", 2),
        "bpl_exempt": False,
        "state_info": code,
        "errors": errors,
        "warnings": warnings,
    }


def calculate_rti_deadline(
    filed_date: str, concerns_life_or_liberty: bool = False, routed_through_apio: bool = False
) -> dict[str, Any]:
    """
    Calculate RTI response and appeal deadlines.

    Input:
    - filed_date (str): YYYY-MM-DD
    - concerns_life_or_liberty (bool): True if relates to life/liberty
    - routed_through_apio (bool): True if filed via APIO

    Output: filed_date, response_due_date, first_appeal_deadline,
    second_appeal_deadline, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        start_date = datetime.date.fromisoformat(filed_date)
    except ValueError:
        errors.append("filed_date must be in YYYY-MM-DD format.")
        return {"errors": errors, "warnings": warnings}

    response_due_date = start_date
    if concerns_life_or_liberty:
        # Life or liberty: 48 hours. Approximating to 2 days for date-based calc.
        response_due_date += datetime.timedelta(days=2)
    else:
        response_due_date += datetime.timedelta(days=30)

    if routed_through_apio:
        response_due_date += datetime.timedelta(days=5)

    first_appeal_deadline = response_due_date + datetime.timedelta(days=30)
    second_appeal_deadline = first_appeal_deadline + datetime.timedelta(days=90)

    return {
        "filed_date": filed_date,
        "response_due_date": response_due_date.isoformat(),
        "first_appeal_deadline": first_appeal_deadline.isoformat(),
        "second_appeal_deadline": second_appeal_deadline.isoformat(),
        "errors": errors,
        "warnings": warnings,
    }


def calculate_rti_penalty_estimate(
    due_date: str, response_received_date: str | None = None
) -> dict[str, Any]:
    """
    Estimate penalty for delayed RTI response under Section 20.

    Input:
    - due_date (str): YYYY-MM-DD
    - response_received_date (str): Optional. YYYY-MM-DD. Defaults to today.

    Output: delay_days, estimated_penalty, penalty_cap_reached, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        due = datetime.date.fromisoformat(due_date)
        if response_received_date:
            received = datetime.date.fromisoformat(response_received_date)
        else:
            received = datetime.date.today()
    except ValueError:
        errors.append("Dates must be in YYYY-MM-DD format.")
        return {"errors": errors, "warnings": warnings}

    delay_days = (received - due).days
    if delay_days <= 0:
        return {
            "delay_days": 0,
            "estimated_penalty": 0,
            "penalty_cap_reached": False,
            "errors": errors,
            "warnings": warnings,
        }

    penalty = delay_days * 250
    cap_reached = penalty >= 25000
    if cap_reached:
        penalty = 25000

    return {
        "delay_days": delay_days,
        "estimated_penalty": penalty,
        "penalty_cap_reached": cap_reached,
        "errors": errors,
        "warnings": warnings,
    }


def draft_rti_application(
    pio_office: str,
    subject: str,
    information_sought: list[str],
    applicant_category: str = "general",
) -> dict[str, Any]:
    """
    Draft a template RTI application text under Section 6 of RTI Act 2005.

    Input:
    - pio_office (str): Name and address of PIO office
    - subject (str): Subject of the application
    - information_sought (list[str]): List of info points
    - applicant_category (str): "general" or "bpl"

    Output: draft_text, format, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    points = "\n".join([f"{i + 1}. {pt}" for i, pt in enumerate(information_sought)])
    fee_statement = (
        (
            "I am a BPL card holder and exempt from paying the application fee. "
            "Attached is a copy of my BPL certificate."
        )
        if applicant_category.lower() == "bpl"
        else "I have attached the prescribed application fee of Rs. 10/- via Postal Order/DD."
    )

    draft = f"""To,
The Public Information Officer (PIO)
{pio_office}

Subject: Request for Information under Section 6 of the Right to Information Act, 2005.
Regarding: {subject}

Respected Sir/Madam,

Please provide the following information under the RTI Act, 2005:

{points}

Fee Details:
{fee_statement}

Declaration:
I state that the information sought does not fall within the restrictions contained in
Section 8 and 9 of the Act and to the best of my knowledge it pertains to your office.

Place: [Your Place]
Date: {datetime.date.today().isoformat()}

Yours faithfully,
[Your Name]
[Your Address]
[Your Contact]"""

    return {
        "draft_text": draft,
        "format": "section_6_application",
        "errors": errors,
        "warnings": warnings,
    }


def draft_first_appeal(original_application_ref: str, grounds: list[str]) -> dict[str, Any]:
    """
    Draft first appeal template under Section 19(1).

    Input:
    - original_application_ref (str): Reference to original RTI
    - grounds (list[str]): Grounds for appeal

    Output: draft_text, appeal_level, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    grounds_str = "\n".join([f"- {g}" for g in grounds])

    draft = f"""To,
The First Appellate Authority (FAA)
[Appellate Authority Office Address]

Subject: First Appeal under Section 19(1) of the RTI Act, 2005.

Reference: My RTI Application dated [Date] (Ref: {original_application_ref}).

Respected Sir/Madam,

I filed an RTI application on the above reference date.
I am filing this first appeal on the following grounds:
{grounds_str}

Relief Sought:
Please direct the PIO to provide the information as requested in my
original application immediately.

Attached:
1. Copy of original RTI Application
2. Copy of PIO response (if any)

Place: [Your Place]
Date: {datetime.date.today().isoformat()}

Yours faithfully,
[Your Name]
[Your Address]"""

    return {"draft_text": draft, "appeal_level": "first", "errors": errors, "warnings": warnings}


def draft_second_appeal(original_application_ref: str, grounds: list[str]) -> dict[str, Any]:
    """
    Draft second appeal template under Section 19(3) to Information Commission.

    Input:
    - original_application_ref (str): Reference to original RTI
    - grounds (list[str]): Grounds for appeal

    Output: draft_text, appeal_level, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    grounds_str = "\n".join([f"- {g}" for g in grounds])

    draft = f"""To,
The Information Commissioner
Central/State Information Commission
[Commission Address]

Subject: Second Appeal under Section 19(3) of the RTI Act, 2005.

Reference: Original RTI Ref: {original_application_ref}. First Appeal filed on [Date].

Respected Sir/Madam,

I am filing this Second Appeal against the decision/non-decision of the First Appellate Authority.

Grounds for Second Appeal:
{grounds_str}

Relief Sought:
1. Direct the PIO to provide complete and accurate information.
2. Impose penalty under Section 20 on the PIO for unreasonable delay/denial.

Attached:
1. Copy of original RTI Application
2. Copy of PIO reply (if any)
3. Copy of First Appeal
4. Copy of FAA order (if any)

Place: [Your Place]
Date: {datetime.date.today().isoformat()}

Yours faithfully,
[Your Name]
[Your Address]"""

    return {"draft_text": draft, "appeal_level": "second", "errors": errors, "warnings": warnings}
