from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.bare_act import decode_ipc_bns_crosswalk as core_decode_ipc_bns_crosswalk
from mcp_india_stack.tools.bare_act import lookup_bns_section as core_lookup_bns_section
from mcp_india_stack.tools.bare_act import lookup_bnss_section as core_lookup_bnss_section
from mcp_india_stack.tools.bare_act import lookup_bsa_section as core_lookup_bsa_section
from mcp_india_stack.tools.bare_act import lookup_crpc_section as core_lookup_crpc_section
from mcp_india_stack.tools.bare_act import (
    lookup_evidence_act_section as core_lookup_evidence_act_section,
)
from mcp_india_stack.tools.bare_act import lookup_ipc_section as core_lookup_ipc_section
from mcp_india_stack.tools.cnr import decode_cnr_number as core_decode_cnr_number
from mcp_india_stack.tools.court_establishment import (
    lookup_court_establishment_code as core_lookup_court_establishment_code,
)
from mcp_india_stack.tools.court_fee import calculate_court_fee as core_calculate_court_fee
from mcp_india_stack.tools.limitation import (
    calculate_limitation_deadline as core_calculate_limitation_deadline,
)
from mcp_india_stack.tools.regulatory_calendar import (
    get_regulatory_deadlines as core_get_regulatory_deadlines,
)
from mcp_india_stack.tools.rti import calculate_rti_deadline as core_calculate_rti_deadline
from mcp_india_stack.tools.rti import calculate_rti_fee as core_calculate_rti_fee
from mcp_india_stack.tools.rti import (
    calculate_rti_penalty_estimate as core_calculate_rti_penalty_estimate,
)
from mcp_india_stack.tools.rti import draft_first_appeal as core_draft_first_appeal
from mcp_india_stack.tools.rti import draft_rti_application as core_draft_rti_application
from mcp_india_stack.tools.rti import draft_second_appeal as core_draft_second_appeal
from mcp_india_stack.tools.stamp_duty import calculate_stamp_duty as core_calculate_stamp_duty
from mcp_india_stack.utils.responses import build_response


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_cnr_number(
    cnr: Annotated[
        str,
        Field(
            description="16-character CNR string. Spaces and hyphens are stripped automatically."
        ),
    ],
) -> dict[str, Any]:
    """Decode and validate a 16-character CNR.

    Use when extracting state, district, establishment, case type, year, and
    serial from a CNR number.

    Args:
        cnr: 16-character CNR string.

    Returns:
        Standard envelope containing decoded fields.

    Notes:
        Format validation with field decoding. Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_decode_cnr_number(cnr=cnr)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"CNR decode failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_court_establishment_code(
    code: Annotated[
        str,
        Field(description="State and district court establishment code (e.g. MH, MHPU, MHPU01)"),
    ],
) -> dict[str, Any]:
    """Look up court establishment codes for states, districts, and complexes.

    Use when you need to decode the state and district court location from a code.

    Args:
        code: Court establishment code.

    Returns:
        Standard envelope containing location metadata.

    Notes:
        Returns static master data. Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_court_establishment_code(code=code)
        return result
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Court establishment code lookup failed: {exc}"],
            source="bundled_dataset",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_ipc_section(
    section: Annotated[str, Field(description="IPC section number to lookup (e.g., 420)")],
) -> dict[str, Any]:
    """Look up an IPC section detail.

    Use when you need the title and description of a section in the Indian Penal Code.

    Args:
        section: IPC section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_ipc_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"IPC lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_bns_section(
    section: Annotated[str, Field(description="BNS section number to lookup (e.g., 316)")],
) -> dict[str, Any]:
    """Look up a BNS section detail.

    Use when you need the title and description of a section in the Bharatiya Nyaya Sanhita.

    Args:
        section: BNS section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_bns_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"BNS lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_crpc_section(
    section: Annotated[str, Field(description="CrPC section number to lookup")],
) -> dict[str, Any]:
    """Look up a CrPC section detail.

    Use when you need the title and description of a section in the Code of Criminal Procedure.

    Args:
        section: CrPC section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_crpc_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"CrPC lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_bnss_section(
    section: Annotated[str, Field(description="BNSS section number to lookup")],
) -> dict[str, Any]:
    """Look up a BNSS section detail.

    Use when you need the title and description of a section in the Bharatiya Nagarik
    Suraksha Sanhita.

    Args:
        section: BNSS section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_bnss_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"BNSS lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_evidence_act_section(
    section: Annotated[str, Field(description="Indian Evidence Act section number to lookup")],
) -> dict[str, Any]:
    """Look up an Indian Evidence Act section detail.

    Use when you need the title and description of a section in the Indian Evidence Act.

    Args:
        section: Indian Evidence Act section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_evidence_act_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Evidence Act lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def lookup_bsa_section(
    section: Annotated[str, Field(description="BSA section number to lookup")],
) -> dict[str, Any]:
    """Look up a BSA section detail.

    Use when you need the title and description of a section in the Bharatiya Sakshya Adhiniyam.

    Args:
        section: BSA section number.

    Returns:
        Standard envelope with section details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_lookup_bsa_section(section=section)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"BSA lookup failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def decode_ipc_bns_crosswalk(
    section: Annotated[str, Field(description="Section number to map across Acts")],
    from_act: Annotated[
        str, Field(description="The source Act (IPC or BNS). Default: IPC")
    ] = "IPC",
) -> dict[str, Any]:
    """Provide a bidirectional crosswalk between IPC and BNS sections.

    Use when you need to find the equivalent section in BNS from IPC or vice versa.

    Args:
        section: Section number to map.
        from_act: Source Act ("IPC" or "BNS").

    Returns:
        Standard envelope with crosswalk mapping details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_decode_ipc_bns_crosswalk(section=section, from_act=from_act)
        return result
    except Exception as exc:
        return build_response(
            success=False, errors=[f"Crosswalk decode failed: {exc}"], source="offline_static"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_limitation_deadline(
    suit_type: Annotated[
        str, Field(description="Type of suit/appeal/application to calculate limitation for")
    ],
    cause_of_action_date: Annotated[
        str, Field(description="Date when the cause of action arose (YYYY-MM-DD)")
    ],
) -> dict[str, Any]:
    """Calculate the deadline under the Limitation Act.

    Use when computing the last date to file a suit, appeal, or application based on
    cause of action.

    Args:
        suit_type: Type of suit/appeal/application.
        cause_of_action_date: Date the cause of action arose (YYYY-MM-DD).

    Returns:
        Standard envelope with deadline date and limitation period.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_limitation_deadline(
            suit_type=suit_type, cause_of_action_date=cause_of_action_date
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Limitation deadline calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_court_fee(
    state_code: Annotated[
        str, Field(description="State code where suit is filed (e.g., MH, DL, KA)")
    ],
    suit_value: Annotated[float, Field(description="Value of the suit in INR")],
    suit_type: Annotated[str, Field(description="Type of suit (default: 'money')")] = "money",
) -> dict[str, Any]:
    """Calculate ad valorem court fees for a specific state.

    Use when you need to estimate the court fee required to be paid for filing a suit.

    Args:
        state_code: State code (e.g., 'MH', 'DL', 'KA').
        suit_value: Value of the suit.
        suit_type: Type of suit.

    Returns:
        Standard envelope with calculated court fee and computation details.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_court_fee(
            state_code=state_code, suit_value=suit_value, suit_type=suit_type
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Court fee calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_stamp_duty(
    state_code: Annotated[
        str, Field(description="State code where instrument is executed (e.g., MH, DL, KA)")
    ],
    instrument_type: Annotated[
        str, Field(description="Type of instrument (e.g., conveyance, lease, agreement)")
    ],
    transaction_value: Annotated[
        float, Field(description="Value of the transaction/consideration in INR")
    ],
) -> dict[str, Any]:
    """Calculate state stamp duty for various instruments.

    Use when estimating the stamp duty payable on legal documents like conveyance or lease.

    Args:
        state_code: State code (e.g., 'MH', 'DL', 'KA').
        instrument_type: Type of instrument.
        transaction_value: Value of the transaction.

    Returns:
        Standard envelope with stamp duty amount and surcharge components.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_stamp_duty(
            state_code=state_code,
            instrument_type=instrument_type,
            transaction_value=transaction_value,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Stamp duty calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_rti_fee(
    state_code: Annotated[
        str, Field(description="State code or 'central' (default: 'central')")
    ] = "central",
    applicant_category: Annotated[
        str, Field(description="Category of the applicant ('general' or 'bpl')")
    ] = "general",
) -> dict[str, Any]:
    """Calculate the required RTI application fee for central or state authorities.

    Use when determining the application fee required to file an RTI request.

    Args:
        state_code: State code or 'central'.
        applicant_category: 'general' or 'bpl' (Below Poverty Line).

    Returns:
        Standard envelope with the applicable fee amount and mode of payment.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_rti_fee(
            state_code=state_code, applicant_category=applicant_category
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"RTI fee calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_rti_deadline(
    filed_date: Annotated[
        str, Field(description="Date the RTI application was filed (YYYY-MM-DD)")
    ],
    concerns_life_or_liberty: Annotated[
        bool, Field(description="Whether the info sought concerns life or liberty of a person")
    ] = False,
    routed_through_apio: Annotated[
        bool, Field(description="Whether the application was submitted through an APIO")
    ] = False,
) -> dict[str, Any]:
    """Calculate standard, life/liberty, or APIO-routed RTI response deadlines.

    Use when determining the due date for receiving a response to an RTI application.

    Args:
        filed_date: Date filed (YYYY-MM-DD).
        concerns_life_or_liberty: True if information concerns life or liberty.
        routed_through_apio: True if submitted via Assistant PIO.

    Returns:
        Standard envelope with the calculated deadline date.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_rti_deadline(
            filed_date=filed_date,
            concerns_life_or_liberty=concerns_life_or_liberty,
            routed_through_apio=routed_through_apio,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"RTI deadline calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_rti_penalty_estimate(
    due_date: Annotated[str, Field(description="The date the RTI response was due (YYYY-MM-DD)")],
    response_received_date: Annotated[
        str | None, Field(description="Date the response was received, if any (YYYY-MM-DD)")
    ] = None,
) -> dict[str, Any]:
    """Estimate potential penalties for delayed RTI responses under Section 20.

    Use when computing the estimated penalty that may be imposed on a PIO for delay.

    Args:
        due_date: Due date of the response (YYYY-MM-DD).
        response_received_date: Actual response date (YYYY-MM-DD) or None if still pending.

    Returns:
        Standard envelope with penalty estimate and days delayed.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_calculate_rti_penalty_estimate(
            due_date=due_date, response_received_date=response_received_date
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"RTI penalty estimate calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def draft_rti_application(
    pio_office: Annotated[str, Field(description="Name and address of the PIO office")],
    subject: Annotated[str, Field(description="Subject line for the RTI application")],
    information_sought: Annotated[
        list[str], Field(description="List of specific information items sought")
    ],
    applicant_category: Annotated[
        str, Field(description="Category of the applicant ('general' or 'bpl')")
    ] = "general",
) -> dict[str, Any]:
    """Generate a draft RTI application format based on provided parameters.

    Use when you need a boilerplate template for filing an RTI request.

    Args:
        pio_office: PIO office details.
        subject: Subject of the RTI.
        information_sought: List of points of information requested.
        applicant_category: 'general' or 'bpl'.

    Returns:
        Standard envelope with the drafted text of the RTI application.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_draft_rti_application(
            pio_office=pio_office,
            subject=subject,
            information_sought=information_sought,
            applicant_category=applicant_category,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"RTI application drafting failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def draft_first_appeal(
    original_application_ref: Annotated[
        str, Field(description="Reference number or details of the original RTI application")
    ],
    grounds: Annotated[list[str], Field(description="List of grounds for filing the first appeal")],
) -> dict[str, Any]:
    """Generate a draft First Appeal under the RTI Act.

    Use when the PIO fails to respond or provides unsatisfactory information.

    Args:
        original_application_ref: Reference to the original RTI application.
        grounds: Grounds for the first appeal.

    Returns:
        Standard envelope with the drafted text of the first appeal.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_draft_first_appeal(
            original_application_ref=original_application_ref, grounds=grounds
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"First appeal drafting failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def draft_second_appeal(
    original_application_ref: Annotated[
        str, Field(description="Reference number or details of the original RTI application")
    ],
    grounds: Annotated[
        list[str], Field(description="List of grounds for filing the second appeal")
    ],
) -> dict[str, Any]:
    """Generate a draft Second Appeal to the Information Commission.

    Use when the First Appellate Authority fails to respond or provides an unsatisfactory decision.

    Args:
        original_application_ref: Reference to the original RTI application.
        grounds: Grounds for the second appeal.

    Returns:
        Standard envelope with the drafted text of the second appeal.

    Notes:
        Not legal advice. Consult a qualified advocate.
    """
    try:
        result = core_draft_second_appeal(
            original_application_ref=original_application_ref, grounds=grounds
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Second appeal drafting failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def get_regulatory_deadlines(
    category: Annotated[
        str | None,
        Field(description="Filter by category (Income Tax, TDS, GST, PF/ESIC, ROC, etc.)"),
    ] = None,
    from_date: Annotated[str | None, Field(description="Start date filter (YYYY-MM-DD)")] = None,
    to_date: Annotated[str | None, Field(description="End date filter (YYYY-MM-DD)")] = None,
) -> dict[str, Any]:
    """Get India's tax & regulatory compliance calendar for FY2025-26.

    Use when planning tax compliance schedules, setting reminders for deadlines,
    or building financial compliance dashboards.

    Args:
        category: Filter by category (Income Tax, TDS, GST, PF/ESIC, ROC, etc.)
        from_date: Start date filter (YYYY-MM-DD)
        to_date: End date filter (YYYY-MM-DD)

    Returns:
        Standard envelope with deadlines grouped by month for FY2025-26

    Notes:
        Covers ITR filing, TDS deposits, GST returns, PF/ESIC, ROC filings,
        advance tax, and professional tax deadlines.
    """
    try:
        result = core_get_regulatory_deadlines(
            category=category, from_date=from_date, to_date=to_date
        )
        return build_response(success=True, data=result, source="offline_dataset")
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Regulatory calendar lookup failed: {exc}"],
            source="offline_algorithm",
        )
