from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.advance_tax import calculate_advance_tax as core_calculate_advance_tax
from mcp_india_stack.tools.capital_gains import (
    calculate_capital_gains as core_calculate_capital_gains,
)
from mcp_india_stack.tools.gst_calculator import calculate_gst as core_calculate_gst
from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee as core_calculate_gst_late_fee
from mcp_india_stack.tools.hra import calculate_hra_exemption as core_calculate_hra
from mcp_india_stack.tools.income_tax import calculate_income_tax as core_calculate_income_tax
from mcp_india_stack.tools.income_tax_interest import (
    calculate_income_tax_interest as core_calculate_income_tax_interest,
)
from mcp_india_stack.tools.leave_encashment import (
    calculate_leave_encashment_tax as core_calculate_leave_encashment_tax,
)
from mcp_india_stack.tools.presumptive_tax import (
    calculate_presumptive_tax as core_calculate_presumptive_tax,
)
from mcp_india_stack.tools.professional_tax import (
    calculate_professional_tax as core_calculate_professional_tax,
)
from mcp_india_stack.tools.salary_restructuring import (
    calculate_salary_restructuring as core_calculate_salary_restructuring,
)
from mcp_india_stack.tools.surcharge import calculate_surcharge as core_calculate_surcharge
from mcp_india_stack.tools.tds import calculate_tds as core_calculate_tds
from mcp_india_stack.utils.responses import build_response


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_income_tax(
    gross_income: Annotated[
        float, Field(description="Annual gross income in rupees. Example: 1500000")
    ],
    regime: Annotated[
        str, Field(description="Tax regime: 'new', 'old', or 'both' for comparison")
    ] = "both",
    taxpayer_type: Annotated[
        str, Field(description="'individual', 'senior_citizen', or 'super_senior_citizen'")
    ] = "individual",
    deduction_80c: Annotated[
        float, Field(description="Section 80C deduction (PF, ELSS, LIC), capped at 1.5L")
    ] = 0,
    deduction_80d_self: Annotated[
        float, Field(description="Section 80D medical insurance self, capped at 25K")
    ] = 0,
    deduction_80d_parents: Annotated[
        float, Field(description="Section 80D medical insurance parents, capped at 25K/50K")
    ] = 0,
    deduction_80d_senior_parents: Annotated[
        bool, Field(description="If True, parents 80D cap is 50K instead of 25K")
    ] = False,
    deduction_80ccd_nps: Annotated[
        float, Field(description="Additional NPS deduction under 80CCD(1B), capped at 50K")
    ] = 0,
    deduction_24b: Annotated[
        float, Field(description="Home loan interest under Section 24(b), capped at 2L")
    ] = 0,
    other_deductions: Annotated[float, Field(description="Other deductions (no cap)")] = 0,
) -> dict[str, Any]:
    """Calculate Indian income tax for FY2025-26 under old, new, or both regimes.

    Use when computing tax liability, comparing regimes, or planning deductions.
    Includes slab computation, Section 87A rebate, surcharge with marginal relief,
    and health & education cess.

    Args:
            gross_income: Annual gross income in rupees.
            regime: 'new', 'old', or 'both' for side-by-side comparison.
            taxpayer_type: Category for slab selection.
            deduction_80c: Old regime only — Section 80C amount.
            deduction_80d_self: Old regime only — medical insurance self.
            deduction_80d_parents: Old regime only — medical insurance parents.
            deduction_80d_senior_parents: Old regime only — senior parent flag.
            deduction_80ccd_nps: Old regime only — NPS additional.
            deduction_24b: Old regime only — home loan interest.
            other_deductions: Old regime only — other amounts.

    Returns:
            Standard envelope with per-regime breakdown, effective rate, monthly tax,
            take-home, and regime recommendation when both requested.

    Notes:
            FY2025-26 rates. Estimate only — consult a CA for filing.
    """
    try:
        result = core_calculate_income_tax(
            gross_income=gross_income,
            regime=regime,
            taxpayer_type=taxpayer_type,
            deduction_80c=deduction_80c,
            deduction_80d_self=deduction_80d_self,
            deduction_80d_parents=deduction_80d_parents,
            deduction_80d_senior_parents=deduction_80d_senior_parents,
            deduction_80ccd_nps=deduction_80ccd_nps,
            deduction_24b=deduction_24b,
            other_deductions=other_deductions,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Income tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_tds(
    section: Annotated[
        str, Field(description="TDS section key, e.g. '194C_individual', '194J_professional'")
    ],
    payment_amount: Annotated[float, Field(description="Gross payment amount in rupees")],
    pan_available: Annotated[bool, Field(description="Whether payee has provided PAN")],
    is_senior_citizen: Annotated[
        bool, Field(description="For 194A bank interest — applies higher threshold for seniors")
    ] = False,
    aggregate_payments_ytd: Annotated[
        float, Field(description="Prior payments to same payee under this section in current FY")
    ] = 0.0,
    payee_type: Annotated[
        str, Field(description="Payee type: 'individual_huf' or 'other' (affects 194C rate)")
    ] = "individual_huf",
) -> dict[str, Any]:
    """Calculate TDS for a given section and payment amount (FY2025-26).

    Use when computing withholding tax on contractor payments, professional fees,
    interest, rent, commissions, or purchase of goods.

    Args:
            section: TDS section key from supported sections.
            payment_amount: Gross payment in rupees.
            pan_available: Whether payee PAN is available (affects rate).
            is_senior_citizen: For 194A bank interest threshold.
            aggregate_payments_ytd: Prior payments to same payee in current FY.
            payee_type: 'individual_huf' or 'other' - affects 194C rate.

    Returns:
            Standard envelope with TDS applicability, rate, amount, net payment.

    Notes:
            FY2025-26 rates. Actual rates may vary by DTAA or Form 15G/15H.
    """
    try:
        result = core_calculate_tds(
            section=section,
            payment_amount=payment_amount,
            pan_available=pan_available,
            is_senior_citizen=is_senior_citizen,
            aggregate_payments_ytd=aggregate_payments_ytd,
            payee_type=payee_type,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"TDS calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_gst(
    amount: Annotated[
        float, Field(description="Base amount in rupees (or inclusive amount if flagged)")
    ],
    gst_rate: Annotated[
        float, Field(description="GST rate as percentage: 0, 0.1, 0.25, 1.5, 3, 5, 12, 18, 28")
    ],
    transaction_type: Annotated[
        str, Field(description="'intra_state' (CGST+SGST) or 'inter_state' (IGST)")
    ],
    amount_includes_gst: Annotated[
        bool, Field(description="If True, back-calculate base from GST-inclusive amount")
    ] = False,
    cess_category: Annotated[
        str, Field(description="Cess category for 28% items. Default: 'default' (no cess)")
    ] = "default",
) -> dict[str, Any]:
    """Calculate GST breakdown with CGST/SGST/IGST split and optional cess.

    Use when computing tax for invoices, quotations, or GST compliance.

    Args:
            amount: Base amount or GST-inclusive amount in rupees.
            gst_rate: Valid GST rate percentage.
            transaction_type: 'intra_state' or 'inter_state'.
            amount_includes_gst: Set True to back-calculate base.
            cess_category: For 28% items, specify applicable cess.

    Returns:
            Standard envelope with base amount, CGST/SGST/IGST breakdown,
            cess amount, total GST, and total payable amount.

    Notes:
            Rates are for general reference. Actual classification may vary.
    """
    try:
        result = core_calculate_gst(
            amount=amount,
            gst_rate=gst_rate,
            transaction_type=transaction_type,
            amount_includes_gst=amount_includes_gst,
            cess_category=cess_category,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"GST calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_surcharge(
    total_income: Annotated[float, Field(description="Total income in rupees")],
    base_tax: Annotated[float, Field(description="Base tax amount before surcharge")],
    regime: Annotated[str, Field(description="'new' or 'old' tax regime")],
) -> dict[str, Any]:
    """Calculate surcharge and marginal relief for a given income and base tax.

    Use when computing surcharge as a standalone calculation, separate from
    the full income tax tool. The income tax tool uses this logic internally.

    Args:
            total_income: Total income in rupees.
            base_tax: Base tax amount before surcharge.
            regime: 'new' (capped at 25%) or 'old' (up to 37%).

    Returns:
            Standard envelope with surcharge rate, before/after marginal relief,
            and cess base.

    Notes:
            FY2025-26 rates. New regime surcharge capped at 25%.
    """
    try:
        result = core_calculate_surcharge(
            total_income=total_income, base_tax=base_tax, regime=regime
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Surcharge calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_hra_exemption(
    basic_salary: Annotated[float, Field(description="Monthly basic salary in rupees")],
    hra_received: Annotated[
        float, Field(description="Annual HRA received from employer in rupees")
    ],
    rent_paid: Annotated[float, Field(description="Annual rent paid in rupees")],
    city_type: Annotated[
        str, Field(description="'metro' (Delhi/Mumbai/Chennai/Kolkata) or 'non_metro'")
    ] = "non_metro",
    is_government_employee: Annotated[
        bool, Field(description="True for government employees using simplified formula")
    ] = False,
) -> dict[str, Any]:
    """Calculate House Rent Allowance (HRA) exemption under Section 10(13A).

    Use when computing tax-exempt HRA component for salary structuring or
    income tax filing. Compares three conditions and takes minimum.

    Args:
            basic_salary: Monthly basic salary.
            hra_received: Annual HRA received from employer.
            rent_paid: Annual rent paid.
            city_type: 'metro' (50% of salary) or 'non_metro' (40% of salary).
            is_government_employee: Use simplified formula for government employees.

    Returns:
            Standard envelope with exemption amount, taxable HRA, and breakdown.

    Notes:
            The actual exemption is the minimum of:
            1. HRA received
            2. Rent paid minus 10% of salary
            3. 50% of salary (metro) or 40% (non_metro)
    """
    try:
        result = core_calculate_hra(
            basic_salary=basic_salary,
            hra_received=hra_received,
            rent_paid=rent_paid,
            city_type=city_type,
            is_government_employee=is_government_employee,
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
            success=False, errors=[f"HRA calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_capital_gains(
    sale_price: Annotated[float, Field(description="Sale proceeds in rupees")],
    purchase_price: Annotated[float, Field(description="Original purchase price in rupees")],
    asset_type: Annotated[
        str,
        Field(description="Asset type: equity, mutual_fund, real_estate, gold, debentures, crypto"),
    ] = "equity",
    holding_period_days: Annotated[int, Field(description="Number of days held before sale")] = 365,
    inflation_index_purchase: Annotated[
        float | None, Field(description="CII for purchase year (for indexation)")
    ] = None,
    inflation_index_sale: Annotated[
        float | None, Field(description="CII for sale year (for indexation)")
    ] = None,
    expenses_on_sale: Annotated[
        float, Field(description="Brokerage, registration and other expenses on sale")
    ] = 0,
    improvements: Annotated[float, Field(description="Cost of improvements (for real estate)")] = 0,
) -> dict[str, Any]:
    """Calculate capital gains tax for various asset types (FY2025-26).

    Use when computing tax liability on sale of equity, mutual funds,
    real estate, gold, or other capital assets.

    Args:
            sale_price: Sale proceeds after expenses.
            purchase_price: Original purchase price.
            asset_type: Type of asset sold.
            holding_period_days: Days held before sale.
            inflation_index_purchase: Cost Inflation Index for purchase year.
            inflation_index_sale: Cost Inflation Index for sale year.
            expenses_on_sale: Expenses incurred during sale.
            improvements: Cost of improvements (for real estate).

    Returns:
            Standard envelope with STCG/LTCG breakdown, tax rates, and liability.

    Notes:
            Budget 2024 rates: STCG 20% (equity/MF), LTCG 12.5% (equity/MF threshold 100K).
            Real estate without indexation taxed at 20%.
    """
    try:
        result = core_calculate_capital_gains(
            sale_price=sale_price,
            purchase_price=purchase_price,
            asset_type=asset_type,
            holding_period_days=holding_period_days,
            inflation_index_purchase=inflation_index_purchase,
            inflation_index_sale=inflation_index_sale,
            expenses_on_sale=expenses_on_sale,
            improvements=improvements,
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
            errors=[f"Capital gains calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_advance_tax(
    estimated_income: Annotated[
        float, Field(description="Estimated total income for FY in rupees")
    ],
    regime: Annotated[str, Field(description="'new' or 'old' tax regime")] = "new",
    taxpayer_type: Annotated[
        str, Field(description="'individual', 'senior_citizen', or 'super_senior_citizen'")
    ] = "individual",
    existing_tds: Annotated[
        float, Field(description="TDS already deducted or to be deducted in rupees")
    ] = 0,
) -> dict[str, Any]:
    """Calculate quarterly advance tax installment schedule per Sections 234B and 234C.

    Use when planning quarterly tax payments to avoid interest penalties.
    Provides due dates and amounts for each installment.

    Args:
            estimated_income: Estimated annual income for FY2025-26.
            regime: Tax regime for calculation.
            taxpayer_type: Category for slab selection.
            existing_tds: TDS already likely to be deducted.

    Returns:
            Standard envelope with quarterly breakdown and interest rules.

    Notes:
            Due dates: June 15 (15%), Sept 15 (45%), Dec 15 (75%), Mar 15 (100%).
            Interest 1% per month for delay under Section 234C.
    """
    try:
        result = core_calculate_advance_tax(
            estimated_income=estimated_income,
            regime=regime,
            taxpayer_type=taxpayer_type,
            existing_tds=existing_tds,
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
            errors=[f"Advance tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_gst_late_fee(
    return_type: Annotated[str, Field(description="GSTR1, GSTR3B, or GSTR9")],
    days_delayed: Annotated[int, Field(description="Number of days delayed")],
    annual_turnover: Annotated[float, Field(description="Annual turnover in INR")],
    has_nil_liability: Annotated[bool, Field(description="True if nil return")] = False,
) -> dict[str, Any]:
    """Calculate GST late filing penalty.

    Use when estimating late filing fees or planning compliance.

    Args:
        return_type: "GSTR1", "GSTR3B", or "GSTR9"
        days_delayed: Number of days delayed
        annual_turnover: Annual turnover for cap calculation
        has_nil_liability: True if nil return

    Returns:
        Late fee breakdown with CGST/SGST split.
    """
    try:
        result = core_calculate_gst_late_fee(
            return_type=return_type,
            days_delayed=days_delayed,
            annual_turnover=annual_turnover,
            has_nil_liability=has_nil_liability,
        )
        return build_response(
            success="errors" not in result,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"GST late fee calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_income_tax_interest(
    total_tax_liability: Annotated[float, Field(description="Total tax liability in INR")],
    tds_deducted: Annotated[float, Field(description="TDS already deducted in INR")] = 0.0,
    advance_tax_paid: Annotated[
        dict[str, float] | None, Field(description="Dict with q1,q2,q3,q4 quarterly payments")
    ] = None,
    filing_date: Annotated[
        str | None, Field(description="Filing date YYYY-MM-DD or None if not filed")
    ] = None,
    due_date: Annotated[str, Field(description="Due date YYYY-MM-DD")] = "2025-07-31",
) -> dict[str, Any]:
    """Calculate interest under Sections 234A, 234B, 234C.

    Use when computing penalty interest for late tax filing or short advance tax payments.

    Args:
        total_tax_liability: Total tax liability
        tds_deducted: TDS already deducted
        advance_tax_paid: Dict with q1,q2,q3,q4 quarterly payments
        filing_date: YYYY-MM-DD when return filed (None if not filed)
        due_date: Due date for filing

    Returns:
        Interest breakdown for Sections 234A, 234B, 234C.
    """
    if advance_tax_paid is None:
        advance_tax_paid = {}
    try:
        result = core_calculate_income_tax_interest(
            total_tax_liability=total_tax_liability,
            advance_tax_paid=advance_tax_paid,
            tds_deducted=tds_deducted,
            filing_date=filing_date,
            due_date=due_date,
        )
        return build_response(success=True, data=result, source="offline_algorithm")
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Income tax interest calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_presumptive_tax(
    scheme: Annotated[str, Field(description="'44AD' for business or '44ADA' for professionals")],
    gross_receipts: Annotated[float, Field(description="Total gross receipts in INR")],
    digital_receipt_percent: Annotated[
        float, Field(description="Percentage via digital mode")
    ] = 100.0,
    regime: Annotated[str, Field(description="'new' or 'old' tax regime")] = "new",
    age: Annotated[int, Field(description="Assessee age")] = 35,
    deductions_80c: Annotated[float, Field(description="Section 80C deductions (old regime)")] = 0,
) -> dict[str, Any]:
    """Calculate tax under presumptive scheme (Sections 44AD, 44ADA).

    Use when computing tax for small businesses or professionals under presumptive taxation.

    Args:
        scheme: "44AD" or "44ADA"
        gross_receipts: Total gross receipts
        digital_receipt_percent: % of receipts via digital mode
        regime: "new" or "old"
        age: Assessee age
        deductions_80c: Section 80C deductions (old regime)

    Returns:
        Presumptive income and total tax payable.
    """
    try:
        result = core_calculate_presumptive_tax(
            scheme=scheme,
            gross_receipts=gross_receipts,
            digital_receipt_percent=digital_receipt_percent,
            regime=regime,
            age=age,
            deductions_80c=deductions_80c,
        )
        return build_response(
            success="errors" not in result,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Presumptive tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_professional_tax(
    gross_salary_monthly: Annotated[float, Field(description="Monthly gross salary in INR")],
    state_code: Annotated[str, Field(description="2-char state code (e.g., MH, KA, TN)")],
) -> dict[str, Any]:
    """Calculate state-wise professional tax.

    Use when computing total tax liability including professional tax deductions.

    Args:
        gross_salary_monthly: Monthly gross salary
        state_code: 2-char state code (e.g., "MH", "KA", "TN")

    Returns:
        Monthly and annual professional tax amount.
    """
    try:
        result = core_calculate_professional_tax(
            gross_salary_monthly=gross_salary_monthly, state_code=state_code
        )
        return build_response(
            success=result.get("applicable", False),
            data=result,
            errors=[],
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Professional tax calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_leave_encashment_tax(
    leave_encashment_amount: Annotated[float, Field(description="Actual amount received in INR")],
    average_monthly_salary: Annotated[
        float, Field(description="Average of last 10 months basic + DA")
    ],
    earned_leave_balance_days: Annotated[int, Field(description="Days of earned leave")],
    years_of_service: Annotated[int, Field(description="Total years of service")],
    is_government_employee: Annotated[bool, Field(description="Government employee flag")] = False,
) -> dict[str, Any]:
    """Calculate tax-exempt portion of leave encashment under Section 10(10AA).

    Use when computing leave encashment tax exemption or planning retirement benefits.

    Args:
        leave_encashment_amount: Actual amount received
        average_monthly_salary: Average of last 10 months basic + DA
        earned_leave_balance_days: Days of earned leave
        years_of_service: Total years of service
        is_government_employee: Government employee flag

    Returns:
        Exemption amount and taxable portion breakdown.
    """
    try:
        result = core_calculate_leave_encashment_tax(
            leave_encashment_amount=leave_encashment_amount,
            average_monthly_salary=average_monthly_salary,
            earned_leave_balance_days=earned_leave_balance_days,
            years_of_service=years_of_service,
            is_government_employee=is_government_employee,
        )
        return build_response(
            success="errors" not in result,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Leave encashment calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_salary_restructuring(
    current_gross: Annotated[float, Field(description="Current gross annual salary in INR")],
    current_basic_ratio: Annotated[
        float, Field(description="Current basic salary as ratio of gross (0.40-0.60)")
    ] = 0.5,
    structure_type: Annotated[
        str, Field(description="Structure option: standard, optimized, or startup")
    ] = "standard",
    include_meal_card: Annotated[
        bool, Field(description="Include Sodexo/Food card allowance")
    ] = False,
    include_wallet_allowance: Annotated[
        bool, Field(description="Include flexible wallet allowance")
    ] = False,
    has_hra: Annotated[bool, Field(description="Employee receives HRA")] = True,
    rent_in_metro: Annotated[
        bool, Field(description="Rent paid in metro city (higher HRA)")
    ] = False,
    family_medical: Annotated[bool, Field(description="Include family medical insurance")] = False,
    parents_medical: Annotated[
        bool, Field(description="Include parents medical insurance (additional)")
    ] = False,
) -> dict[str, Any]:
    """Calculate salary restructuring options for tax optimization.

    Use when advising employees on tax-efficient salary structures,
    comparing restructuring options, or planning CTC optimization.

    Args:
        current_gross: Current gross annual salary in INR
        current_basic_ratio: Current basic salary as ratio of gross
        structure_type: Structure option (standard, optimized, startup)
        include_meal_card: Include Sodexo/Food card allowance
        include_wallet_allowance: Include flexible wallet allowance
        has_hra: Employee receives HRA
        rent_in_metro: Rent paid in metro city (higher HRA)
        family_medical: Include family medical insurance
        parents_medical: Include parents medical insurance

    Returns:
        Standard envelope with tax-optimized structure, deductions, and estimated tax
    """
    try:
        result = core_calculate_salary_restructuring(
            current_gross=current_gross,
            current_basic_ratio=current_basic_ratio,
            structure_type=structure_type,
            include_meal_card=include_meal_card,
            include_wallet_allowance=include_wallet_allowance,
            has_hra=has_hra,
            rent_in_metro=rent_in_metro,
            family_medical=family_medical,
            parents_medical=parents_medical,
        )
        return build_response(success=True, data=result, source="offline_algorithm")
    except Exception as exc:
        return build_response(
            success=False,
            errors=[f"Salary restructuring calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.resource("india://schema/calculate_income_tax")
def schema_calculate_income_tax() -> dict[str, Any]:
    """JSON schema for calculate_income_tax output."""
    return {
        "type": "object",
        "properties": {
            "gross_income": {"type": "number"},
            "regime": {"type": "string"},
            "taxable_income": {"type": "number"},
            "base_tax": {"type": "number"},
            "surcharge": {"type": "number"},
            "cess": {"type": "number"},
            "total_tax": {"type": "number"},
            "effective_rate": {"type": "number"},
            "take_home": {"type": "number"},
            "monthly_take_home": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_tds")
def schema_calculate_tds() -> dict[str, Any]:
    """JSON schema for calculate_tds output."""
    return {
        "type": "object",
        "properties": {
            "section": {"type": "string"},
            "applicability": {"type": "string"},
            "rate": {"type": "number"},
            "tds_amount": {"type": "number"},
            "net_payment": {"type": "number"},
            "threshold_applicable": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_gst")
def schema_calculate_gst() -> dict[str, Any]:
    """JSON schema for calculate_gst output."""
    return {
        "type": "object",
        "properties": {
            "base_amount": {"type": "number"},
            "gst_rate": {"type": "number"},
            "cgst": {"type": "number"},
            "sgst": {"type": "number"},
            "igst": {"type": "number"},
            "cess": {"type": "number"},
            "total_gst": {"type": "number"},
            "total_amount": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_surcharge")
def schema_calculate_surcharge() -> dict[str, Any]:
    """JSON schema for calculate_surcharge output."""
    return {
        "type": "object",
        "properties": {
            "total_income": {"type": "number"},
            "base_tax": {"type": "number"},
            "surcharge_rate": {"type": "number"},
            "surcharge_before_mrc": {"type": "number"},
            "marginal_relief": {"type": "number"},
            "surcharge_after_mrc": {"type": "number"},
            "cess_base": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_hra_exemption")
def schema_calculate_hra_exemption() -> dict[str, Any]:
    """JSON schema for calculate_hra_exemption output."""
    return {
        "type": "object",
        "properties": {
            "exemption": {"type": "number"},
            "taxable_hra": {"type": "number"},
            "annual_basic_salary": {"type": "number"},
            "annual_hra_received": {"type": "number"},
            "annual_rent_paid": {"type": "number"},
            "city_type": {"type": "string"},
            "is_government_employee": {"type": "boolean"},
            "breakdown": {"type": "object"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_capital_gains")
def schema_calculate_capital_gains() -> dict[str, Any]:
    """JSON schema for calculate_capital_gains output."""
    return {
        "type": "object",
        "properties": {
            "short_term_gains": {"type": "number"},
            "long_term_gains": {"type": "number"},
            "total_gains": {"type": "number"},
            "is_long_term": {"type": "boolean"},
            "holding_period_days": {"type": "integer"},
            "tax_liability": {"type": "number"},
            "asset_type": {"type": "string"},
            "stcg_rate": {"type": "number"},
            "ltcg_rate": {"type": "number"},
            "cost_inflation_adjusted": {"type": "number"},
            "exemption_threshold": {"type": "number"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


@mcp.resource("india://schema/calculate_advance_tax")
def schema_calculate_advance_tax() -> dict[str, Any]:
    """JSON schema for calculate_advance_tax output."""
    return {
        "type": "object",
        "properties": {
            "total_tax_liability": {"type": "number"},
            "existing_tds": {"type": "number"},
            "net_tax_liability": {"type": "number"},
            "advance_tax_due": {"type": "number"},
            "regime": {"type": "string"},
            "taxpayer_type": {"type": "string"},
            "is_advance_tax_required": {"type": "boolean"},
            "installments": {"type": "array"},
            "interest_rules": {"type": "object"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }
