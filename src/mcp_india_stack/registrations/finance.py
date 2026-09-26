from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_india_stack.app import mcp
from mcp_india_stack.tools.emi import calculate_emi as core_calculate_emi
from mcp_india_stack.tools.fd_maturity import calculate_fd_maturity as core_calculate_fd_maturity
from mcp_india_stack.tools.gratuity import calculate_gratuity as core_calculate_gratuity
from mcp_india_stack.tools.home_vs_rent import calculate_home_vs_rent as core_calculate_home_vs_rent
from mcp_india_stack.tools.nps_projection import (
    calculate_nps_projection as core_calculate_nps_projection,
)
from mcp_india_stack.tools.ppf_maturity import calculate_ppf_maturity as core_calculate_ppf_maturity
from mcp_india_stack.tools.rd_maturity import calculate_rd_maturity as core_calculate_rd_maturity
from mcp_india_stack.tools.sip_returns import calculate_sip_returns as core_calculate_sip_returns
from mcp_india_stack.tools.step_up_sip import calculate_step_up_sip as core_calculate_step_up_sip
from mcp_india_stack.tools.sukanya_scss import (
    calculate_sukanya_samriddhi as core_calculate_sukanya_samriddhi,
)
from mcp_india_stack.utils.responses import build_response


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_emi(
    principal: Annotated[float, Field(description="Loan amount in INR")],
    annual_interest_rate: Annotated[
        float, Field(description="Annual interest rate as percentage (e.g., 8.5)")
    ],
    tenure_months: Annotated[int, Field(description="Loan tenure in months")],
    loan_type: Annotated[
        str, Field(description="Loan type: home, personal, car, education, other")
    ] = "other",
) -> dict[str, Any]:
    """Calculate EMI for a loan with year-by-year amortization schedule.

    Use when computing loan EMIs, comparing loan options, or planning
    prepayment strategies.

    Args:
        principal: Loan amount in INR.
        annual_interest_rate: Annual rate as percentage.
        tenure_months: Loan tenure in months (max 360).
        loan_type: Label for the loan type.

    Returns:
        Standard envelope with EMI, total payment, interest, and amortization.

    Notes:
        Uses standard reducing balance formula. Actual EMI may vary by lender.
    """
    try:
        result = core_calculate_emi(
            principal=principal,
            annual_interest_rate=annual_interest_rate,
            tenure_months=tenure_months,
            loan_type=loan_type,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"EMI calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_gratuity(
    last_drawn_salary: Annotated[
        float, Field(description="Last basic salary + DA per month in INR")
    ],
    years_of_service: Annotated[
        float, Field(description="Total years served (e.g., 5.8 = 5 yrs 9 months)")
    ],
    is_covered_under_act: Annotated[
        bool, Field(description="True if establishment has 10+ employees")
    ] = True,
) -> dict[str, Any]:
    """Calculate gratuity under the Payment of Gratuity Act, 1972.

    Use when computing terminal benefits, comparing CTC packages, or
    planning retirement benefits.

    Args:
        last_drawn_salary: Basic + DA per month.
        years_of_service: Total service duration.
        is_covered_under_act: True for establishments with 10+ employees.

    Returns:
        Standard envelope with gratuity amount, tax-exempt limit, and breakdown.

    Notes:
        Minimum 5 years service required (except death/disablement).
        Tax-exempt ceiling is ₹20,00,000.
    """
    try:
        result = core_calculate_gratuity(
            last_drawn_salary=last_drawn_salary,
            years_of_service=years_of_service,
            is_covered_under_act=is_covered_under_act,
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
            errors=[f"Gratuity calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_ppf_maturity(
    annual_investment: Annotated[float, Field(description="Amount invested per year in INR")],
    tenure_years: Annotated[int, Field(description="PPF tenure in years (15, 20, 25, or 30)")] = 15,
    annual_interest_rate: Annotated[
        float, Field(description="Annual interest rate percentage (default 7.1 for FY2025-26)")
    ] = 7.1,
) -> dict[str, Any]:
    """Calculate PPF maturity amount with year-by-year breakdown.

    Use when planning long-term savings, comparing investment options, or
    calculating retirement corpus.

    Args:
        annual_investment: Amount invested per year (max ₹1,50,000).
        tenure_years: PPF tenure (15, 20, 25, or 30 years).
        annual_interest_rate: PPF rate (default 7.1% for FY2025-26).

    Returns:
        Standard envelope with maturity amount, total invested, interest earned.

    Notes:
        EEE tax status: exempt at investment, accumulation, and maturity.
        Rate is government-administered and revised quarterly.
    """
    try:
        result = core_calculate_ppf_maturity(
            annual_investment=annual_investment,
            tenure_years=tenure_years,
            annual_interest_rate=annual_interest_rate,
        )
        return build_response(
            success=len(result.get("errors", [])) == 0,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"PPF calculation failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_fd_maturity(
    principal: Annotated[float, Field(description="Deposit amount in INR")],
    annual_interest_rate: Annotated[
        float, Field(description="Interest rate as percentage (e.g., 6.5)")
    ],
    tenure_days: Annotated[int, Field(description="Deposit tenure in days")],
    compounding: Annotated[
        str, Field(description="monthly, quarterly, half_yearly, yearly, simple")
    ] = "quarterly",
    is_senior_citizen: Annotated[bool, Field(description="Senior citizen flag")] = False,
    tds_applicable: Annotated[
        bool, Field(description="Apply 10% TDS if interest exceeds threshold")
    ] = True,
) -> dict[str, Any]:
    """Calculate Fixed Deposit maturity amount.

    Use when projecting FD returns or comparing deposit options.

    Args:
        principal: Deposit amount in INR
        annual_interest_rate: Rate as percentage
        tenure_days: Deposit tenure in days
        compounding: Compounding frequency
        is_senior_citizen: Senior citizen flag (0.25% extra rate)
        tds_applicable: Apply TDS if interest > ₹40,000/yr

    Returns:
        Maturity amount with interest breakdown and TDS if applicable.
    """
    try:
        result = core_calculate_fd_maturity(
            principal=principal,
            annual_interest_rate=annual_interest_rate,
            tenure_days=tenure_days,
            compounding=compounding,
            is_senior_citizen=is_senior_citizen,
            tds_applicable=tds_applicable,
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
            errors=[f"FD maturity calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_rd_maturity(
    monthly_installment: Annotated[float, Field(description="Monthly deposit amount in INR")],
    annual_interest_rate: Annotated[float, Field(description="Annual interest rate as percentage")],
    tenure_months: Annotated[int, Field(description="Deposit tenure in months")],
) -> dict[str, Any]:
    """Calculate Recurring Deposit maturity amount.

    Use when projecting RD returns or planning recurring deposits.

    Args:
        monthly_installment: Monthly deposit amount
        annual_interest_rate: Annual rate as percentage
        tenure_months: Deposit tenure in months

    Returns:
        Maturity amount with total interest earned.
    """
    try:
        result = core_calculate_rd_maturity(
            monthly_installment=monthly_installment,
            annual_interest_rate=annual_interest_rate,
            tenure_months=tenure_months,
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
            errors=[f"RD maturity calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_sip_returns(
    monthly_investment: Annotated[float, Field(description="Monthly SIP amount in INR")],
    expected_annual_return: Annotated[float, Field(description="Expected CAGR as percentage")],
    tenure_years: Annotated[int, Field(description="Investment tenure in years")],
    inflation_rate: Annotated[float, Field(description="Expected inflation rate percentage")] = 6.0,
) -> dict[str, Any]:
    """Calculate SIP maturity with inflation-adjusted returns.

    Use when projecting mutual fund SIP returns or planning systematic investments.

    Args:
        monthly_investment: Monthly SIP amount
        expected_annual_return: Expected CAGR %
        tenure_years: Investment tenure
        inflation_rate: Expected inflation %

    Returns:
        Corpus with wealth gained and inflation-adjusted value.
    """
    try:
        result = core_calculate_sip_returns(
            monthly_investment=monthly_investment,
            expected_annual_return=expected_annual_return,
            tenure_years=tenure_years,
            inflation_rate=inflation_rate,
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
            errors=[f"SIP returns calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_step_up_sip(
    initial_monthly_investment: Annotated[float, Field(description="Starting SIP amount in INR")],
    annual_step_up_percent: Annotated[float, Field(description="Annual step-up percentage")],
    expected_annual_return: Annotated[float, Field(description="Expected CAGR as percentage")],
    tenure_years: Annotated[int, Field(description="Investment tenure in years")],
) -> dict[str, Any]:
    """Calculate SIP with annual step-up increment.

    Use when comparing step-up SIP vs flat SIP or planning salary-linked investments.

    Args:
        initial_monthly_investment: Starting SIP amount
        annual_step_up_percent: % increase each year
        expected_annual_return: Expected CAGR %
        tenure_years: Investment tenure

    Returns:
        Corpus comparison between step-up and flat SIP.
    """
    try:
        result = core_calculate_step_up_sip(
            initial_monthly_investment=initial_monthly_investment,
            annual_step_up_percent=annual_step_up_percent,
            expected_annual_return=expected_annual_return,
            tenure_years=tenure_years,
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
            errors=[f"Step-up SIP calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_nps_projection(
    monthly_contribution: Annotated[float, Field(description="Monthly NPS contribution in INR")],
    current_age: Annotated[int, Field(description="Current age")],
    retirement_age: Annotated[int, Field(description="Retirement age")] = 60,
    expected_annual_return: Annotated[
        float, Field(description="Expected annual return percentage")
    ] = 10.0,
    annuity_rate: Annotated[float, Field(description="Annuity rate percentage")] = 6.0,
    annuity_percent: Annotated[float, Field(description="Corpus for annuity (min 40%)")] = 40.0,
) -> dict[str, Any]:
    """Calculate NPS corpus and monthly pension at retirement.

    Use when planning retirement with NPS or projecting pension.

    Args:
        monthly_contribution: Monthly NPS contribution
        current_age: Current age
        retirement_age: Retirement age (default 60)
        expected_annual_return: Expected annual return %
        annuity_rate: Annuity rate %
        annuity_percent: % of corpus to buy annuity (min 40%)

    Returns:
        Projected corpus, lump sum, and monthly pension estimate.
    """
    try:
        result = core_calculate_nps_projection(
            monthly_contribution=monthly_contribution,
            current_age=current_age,
            retirement_age=retirement_age,
            expected_annual_return=expected_annual_return,
            annuity_rate=annuity_rate,
            annuity_percent=annuity_percent,
        )
        return build_response(
            success="errors" not in result,
            data=result,
            errors=result.get("errors", []),
            source="offline_algorithm",
        )
    except Exception as exc:
        return build_response(
            success=False, errors=[f"NPS projection failed: {exc}"], source="offline_algorithm"
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_sukanya_samriddhi(
    scheme: Annotated[
        str,
        Field(
            description="'ssy' for Sukanya Samriddhi or 'scss' for Senior Citizen Savings Scheme"
        ),
    ],
    annual_investment: Annotated[float, Field(description="Annual deposit amount in INR")],
    annual_interest_rate: Annotated[float, Field(description="Interest rate as percentage")] = 8.2,
) -> dict[str, Any]:
    """Calculate SSY or SCSS maturity amount.

    Use when planning long-term savings for girl child (SSY) or retirement (SCSS).

    Args:
        scheme: "ssy" or "scss"
        annual_investment: Annual deposit amount
        annual_interest_rate: Interest rate (default 8.2%)

    Returns:
        Maturity amount with interest breakdown and tax status.
    """
    try:
        result = core_calculate_sukanya_samriddhi(
            scheme=scheme,
            annual_investment=annual_investment,
            annual_interest_rate=annual_interest_rate,
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
            errors=[f"SSY/SCSS calculation failed: {exc}"],
            source="offline_algorithm",
        )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False))
def calculate_home_vs_rent(
    home_price: Annotated[float, Field(description="Property price in INR")],
    down_payment_percent: Annotated[float, Field(description="Down payment as percentage")] = 20.0,
    loan_interest_rate: Annotated[
        float, Field(description="Home loan interest rate percentage")
    ] = 8.5,
    loan_tenure_years: Annotated[int, Field(description="Loan tenure in years")] = 20,
    monthly_rent: Annotated[float, Field(description="Current monthly rent in INR")] = 25000,
    annual_rent_increase: Annotated[
        float, Field(description="Expected rent increase percentage/year")
    ] = 5.0,
    expected_property_appreciation: Annotated[
        float, Field(description="Property appreciation percentage/year")
    ] = 6.0,
    investment_return: Annotated[
        float, Field(description="Return on invested down payment percentage")
    ] = 12.0,
    analysis_years: Annotated[int, Field(description="Years to compare")] = 20,
) -> dict[str, Any]:
    """Compare buying vs renting financial outcome.

    Use when deciding between buying a home or renting.

    Args:
        home_price: Property price in INR
        down_payment_percent: Down payment as %
        loan_interest_rate: Home loan interest rate %
        loan_tenure_years: Loan tenure
        monthly_rent: Current monthly rent
        annual_rent_increase: Expected rent increase %/year
        expected_property_appreciation: Property appreciation %/year
        investment_return: Return on invested down payment %
        analysis_years: Years to compare

    Returns:
        Buy/rent comparison with yearly breakdown and break-even analysis.
    """
    try:
        result = core_calculate_home_vs_rent(
            home_price=home_price,
            down_payment_percent=down_payment_percent,
            loan_interest_rate=loan_interest_rate,
            loan_tenure_years=loan_tenure_years,
            monthly_rent=monthly_rent,
            annual_rent_increase=annual_rent_increase,
            expected_property_appreciation=expected_property_appreciation,
            investment_return=investment_return,
            analysis_years=analysis_years,
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
            errors=[f"Home vs rent calculation failed: {exc}"],
            source="offline_algorithm",
        )
