"""Core tool functions."""

PAN_ENTITY_TYPE_LABELS = {
    "P": "Individual",
    "C": "Company",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Firm",
    "A": "Association of Persons (AOP)",
    "B": "Body of Individuals (BOI)",
    "G": "Government",
    "J": "Artificial Juridical Person",
    "L": "Local Authority",
    "T": "Trust",
    "E": "Limited Liability Partnership (LLP)",
}

from mcp_india_stack.tools.aadhaar import validate_aadhaar
from mcp_india_stack.tools.advance_tax import calculate_advance_tax, calculate_interest_penalty
from mcp_india_stack.tools.bbps import lookup_bbps_biller
from mcp_india_stack.tools.bulk_aadhaar import bulk_validate_aadhaar
from mcp_india_stack.tools.capital_gains import calculate_capital_gains, calculate_home_loan_savings
from mcp_india_stack.tools.cin import validate_cin
from mcp_india_stack.tools.din import validate_din
from mcp_india_stack.tools.driving_license import validate_driving_license
from mcp_india_stack.tools.emi import calculate_emi
from mcp_india_stack.tools.epf_esic import calculate_epf_esic
from mcp_india_stack.tools.fssai import validate_fssai
from mcp_india_stack.tools.gratuity import calculate_gratuity
from mcp_india_stack.tools.gst_calculator import calculate_gst
from mcp_india_stack.tools.gstin import validate_gstin
from mcp_india_stack.tools.hra import calculate_hra_exemption, calculate_hra_for_salary_structure
from mcp_india_stack.tools.hsn import lookup_hsn_code
from mcp_india_stack.tools.ifsc import lookup_ifsc
from mcp_india_stack.tools.income_tax import calculate_income_tax
from mcp_india_stack.tools.pan import validate_pan
from mcp_india_stack.tools.passport import validate_passport
from mcp_india_stack.tools.pincode import lookup_pincode
from mcp_india_stack.tools.ppf_maturity import calculate_ppf_maturity
from mcp_india_stack.tools.regulatory_calendar import get_regulatory_deadlines
from mcp_india_stack.tools.salary_restructuring import calculate_salary_restructuring
from mcp_india_stack.tools.state_code import decode_state_code
from mcp_india_stack.tools.stock_market import get_stock_history, get_stock_quote
from mcp_india_stack.tools.surcharge import calculate_surcharge
from mcp_india_stack.tools.tds import calculate_tds
from mcp_india_stack.tools.upi import validate_upi_vpa
from mcp_india_stack.tools.voter_id import validate_voter_id

__all__ = [
    "PAN_ENTITY_TYPE_LABELS",
    "bulk_validate_aadhaar",
    "calculate_advance_tax",
    "calculate_capital_gains",
    "calculate_emi",
    "calculate_epf_esic",
    "calculate_gst",
    "calculate_gratuity",
    "calculate_home_loan_savings",
    "calculate_hra_exemption",
    "calculate_hra_for_salary_structure",
    "calculate_income_tax",
    "calculate_interest_penalty",
    "calculate_ppf_maturity",
    "calculate_surcharge",
    "calculate_tds",
    "decode_state_code",
    "lookup_bbps_biller",
    "lookup_hsn_code",
    "lookup_ifsc",
    "lookup_pincode",
    "validate_aadhaar",
    "validate_cin",
    "validate_din",
    "validate_driving_license",
    "validate_fssai",
    "validate_gstin",
    "validate_pan",
    "validate_passport",
    "validate_upi_vpa",
    "validate_voter_id",
    "get_regulatory_deadlines",
    "calculate_salary_restructuring",
    "get_stock_quote",
    "get_stock_history",
]
