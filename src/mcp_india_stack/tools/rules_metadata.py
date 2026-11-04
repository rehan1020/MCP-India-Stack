"""Central registry of statutory and financial rule sets with FY tags and provenance.

Implements G6:
- Enumeration of rule tables with FY tags
- Provenance metadata (rules_version, effective_from, effective_to, source_ref)
- Financial year validation and structured unsupported_financial_year errors
- Rules staleness checks for weekly workflow and deterministic test suites
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class RuleMetadata:
    table_id: str
    name: str
    category: str
    financial_year: str
    supported_years: tuple[str, ...]
    rules_version: str
    effective_from: str
    effective_to: str
    last_verified: str
    source_ref: str


RULE_SETS: dict[str, RuleMetadata] = {
    "income_tax": RuleMetadata(
        table_id="income_tax",
        name="Income Tax Slabs & Rebates",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://incometaxindia.gov.in (Finance (No. 2) Act 2024 / Finance Act 2025)",
    ),
    "tds": RuleMetadata(
        table_id="tds",
        name="TDS Rates & Thresholds",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://incometaxindia.gov.in (Income-tax Act 1961 XVII-B / Finance (No. 2) Act 2024)"
        ),
    ),
    "gst_calculator": RuleMetadata(
        table_id="gst_calculator",
        name="GST Rate Slabs & Cess",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=("https://cbic-gst.gov.in (CGST Act 2017 & CBIC Notifications)"),
    ),
    "surcharge": RuleMetadata(
        table_id="surcharge",
        name="Income Tax Surcharge & Marginal Relief",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://incometaxindia.gov.in (Finance (No. 2) Act 2024 First Schedule Part III)"
        ),
    ),
    "hra": RuleMetadata(
        table_id="hra",
        name="HRA Exemption Rules",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://incometaxindia.gov.in (Income-tax Act 1961 Section 10(13A) read with Rule 2A)"
        ),
    ),
    "capital_gains": RuleMetadata(
        table_id="capital_gains",
        name="Capital Gains Tax Rates",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://incometaxindia.gov.in (Income-tax Act 1961 Sec 111A/112/112A post-Budget 2024)"
        ),
    ),
    "advance_tax": RuleMetadata(
        table_id="advance_tax",
        name="Advance Tax Installments & Penalties",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://incometaxindia.gov.in (Income-tax Act 1961 Sections 207-211)",
    ),
    "gst_late_fee": RuleMetadata(
        table_id="gst_late_fee",
        name="GST Late Fee Rules & Caps",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://cbic-gst.gov.in (CGST Act 2017 Sec 47 / CBIC Notification 19/2021-CT)"
        ),
    ),
    "income_tax_interest": RuleMetadata(
        table_id="income_tax_interest",
        name="Income Tax Interest (234A/B/C)",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://incometaxindia.gov.in (Income-tax Act 1961 Sections 234A, 234B, 234C)",
    ),
    "presumptive_tax": RuleMetadata(
        table_id="presumptive_tax",
        name="Presumptive Taxation (44AD/ADA/AE)",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://incometaxindia.gov.in (Income-tax Act 1961 Sections 44AD, 44ADA, 44AE)",
    ),
    "professional_tax": RuleMetadata(
        table_id="professional_tax",
        name="State Professional Tax Slabs",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://indiacode.nic.in (State Professional Tax Acts & Municipal Schedules)",
    ),
    "leave_encashment": RuleMetadata(
        table_id="leave_encashment",
        name="Leave Encashment Exemption Limits",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://incometaxindia.gov.in (IT Act 1961 Sec 10(10AA) / CBDT Notification 31/2023)"
        ),
    ),
    "salary_restructuring": RuleMetadata(
        table_id="salary_restructuring",
        name="Salary Restructuring Component Standards",
        category="tax",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://incometaxindia.gov.in (Income-tax Act 1961 / Finance (No. 2) Act 2024)",
    ),
    "emi": RuleMetadata(
        table_id="emi",
        name="EMI Loan Calculation Formula",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.rbi.org.in (RBI Banking Regulations / Reducing Balance Formula)",
    ),
    "gratuity": RuleMetadata(
        table_id="gratuity",
        name="Payment of Gratuity Rules",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://indiacode.nic.in (Payment of Gratuity Act, 1972 Section 4)",
    ),
    "ppf_maturity": RuleMetadata(
        table_id="ppf_maturity",
        name="Public Provident Fund Scheme",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://www.indiapost.gov.in (Public Provident Fund Scheme 2019 / MoF Notifications)"
        ),
    ),
    "fd_maturity": RuleMetadata(
        table_id="fd_maturity",
        name="Fixed Deposit Compounding Standards",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.rbi.org.in (RBI Master Direction - Interest Rate on Deposits)",
    ),
    "rd_maturity": RuleMetadata(
        table_id="rd_maturity",
        name="Recurring Deposit Compounding Standards",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.rbi.org.in (RBI Master Direction - Interest Rate on Deposits)",
    ),
    "sip_returns": RuleMetadata(
        table_id="sip_returns",
        name="Systematic Investment Plan Standards",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://www.sebi.gov.in (SEBI Mutual Funds Regulations / Standard Annuity Formula)"
        ),
    ),
    "step_up_sip": RuleMetadata(
        table_id="step_up_sip",
        name="Step-up Systematic Investment Plan",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.sebi.gov.in (SEBI Mutual Funds Regulations / Compounded Model)",
    ),
    "nps_projection": RuleMetadata(
        table_id="nps_projection",
        name="National Pension System Projection Model",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.pfrda.org.in (PFRDA Guidelines / National Pension System)",
    ),
    "sukanya_samriddhi": RuleMetadata(
        table_id="sukanya_samriddhi",
        name="Sukanya Samriddhi Yojana & SCSS",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref=(
            "https://www.indiapost.gov.in (Ministry of Finance Small Savings Rates FY2025-26)"
        ),
    ),
    "home_vs_rent": RuleMetadata(
        table_id="home_vs_rent",
        name="Home Purchase vs Rental Valuation",
        category="finance",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.rbi.org.in (Standard DCF and Opportunity Cost Financial Model)",
    ),
    "epf_esic": RuleMetadata(
        table_id="epf_esic",
        name="EPF and ESIC Statutory Contributions",
        category="banking",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://epfindia.gov.in (EPF Act 1952) & https://esic.gov.in (ESI Act 1948)",
    ),
    "neft_rtgs_imps_charges": RuleMetadata(
        table_id="neft_rtgs_imps_charges",
        name="NEFT, RTGS, and IMPS Regulatory Caps",
        category="banking",
        financial_year="2025-26",
        supported_years=("2025-26", "2026-27"),
        rules_version="2025.1",
        effective_from="2025-04-01",
        effective_to="2027-03-31",
        last_verified="2026-10-15",
        source_ref="https://www.rbi.org.in (RBI Circular DPSS.CO.PD.No.1015/02.14.003/2019-20)",
    ),
}


def get_rule_metadata(table_id: str) -> RuleMetadata:
    """Retrieve rule set metadata for a given calculator table."""
    if table_id not in RULE_SETS:
        raise KeyError(f"Unknown rule table ID: {table_id}")
    return RULE_SETS[table_id]


def validate_financial_year(
    table_id: str,
    financial_year: str,
) -> tuple[bool, dict[str, Any] | None]:
    """Validate requested financial year against supported years for a rule set.

    Returns (True, None) if supported, or (False, error_payload) if unsupported.
    """
    rule = get_rule_metadata(table_id)
    if financial_year in rule.supported_years:
        return True, None

    supported = list(rule.supported_years)
    msg = (
        f"Financial year '{financial_year}' is not supported for {rule.name}. "
        f"Supported financial years: {supported}"
    )
    payload = {
        "error": "unsupported_financial_year",
        "financial_year": financial_year,
        "supported_financial_years": supported,
        "message": msg,
        "errors": [f"unsupported_financial_year: {msg}"],
        "rules_version": rule.rules_version,
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "source_ref": rule.source_ref,
    }
    return False, payload


def attach_rule_metadata(
    result: dict[str, Any],
    table_id: str,
    financial_year: str = "2025-26",
) -> dict[str, Any]:
    """Attach additive provenance fields (rules_version, effective_from/to, source_ref)."""
    rule = get_rule_metadata(table_id)
    result["financial_year"] = financial_year
    result["rules_version"] = rule.rules_version
    result["effective_from"] = rule.effective_from
    result["effective_to"] = rule.effective_to
    result["source_ref"] = rule.source_ref
    return result


def check_rules_staleness(as_of_date: date | None = None) -> list[dict[str, Any]]:
    """Check all registered rule sets against expiry and 180-day verification staleness.

    Deterministic when as_of_date is passed.
    """
    check_date = as_of_date or date.today()
    issues: list[dict[str, Any]] = []

    for table_id, rule in sorted(RULE_SETS.items()):
        eff_to = date.fromisoformat(rule.effective_to)
        last_ver = date.fromisoformat(rule.last_verified)

        if check_date > eff_to:
            issues.append(
                {
                    "table_id": table_id,
                    "name": rule.name,
                    "type": "expired",
                    "effective_to": rule.effective_to,
                    "as_of": check_date.isoformat(),
                    "message": (
                        f"Rule set '{table_id}' ({rule.name}) expired on {rule.effective_to}"
                    ),
                }
            )

        days_since_verified = (check_date - last_ver).days
        if days_since_verified > 180:
            issues.append(
                {
                    "table_id": table_id,
                    "name": rule.name,
                    "type": "stale_verification",
                    "last_verified": rule.last_verified,
                    "days_since_verified": days_since_verified,
                    "as_of": check_date.isoformat(),
                    "message": (
                        f"Rule set '{table_id}' ({rule.name}) was last verified on "
                        f"{rule.last_verified} ({days_since_verified} days ago)"
                    ),
                }
            )

    return issues
