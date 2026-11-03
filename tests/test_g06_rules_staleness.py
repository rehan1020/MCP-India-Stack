"""Tests for G6: Statutory rules enumeration, provenance metadata, and staleness audit.

Verifies:
- All statutory/financial rule sets are registered with FY tags and provenance
- Additive fields (rules_version, effective_from, effective_to, source_ref) in outputs
- Unsupported financial years return structured unsupported_financial_year errors
- Frozen-clock staleness check detects expired rules and verification >180 days
- Golden vector calculations across key statutory tax and financial tools
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mcp_india_stack.tools.advance_tax import calculate_advance_tax
from mcp_india_stack.tools.bank_charges import calculate_neft_rtgs_imps_charges
from mcp_india_stack.tools.capital_gains import calculate_capital_gains
from mcp_india_stack.tools.emi import calculate_emi
from mcp_india_stack.tools.epf_esic import calculate_epf_esic
from mcp_india_stack.tools.fd_maturity import calculate_fd_maturity
from mcp_india_stack.tools.gratuity import calculate_gratuity
from mcp_india_stack.tools.gst_calculator import calculate_gst
from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee
from mcp_india_stack.tools.home_vs_rent import calculate_home_vs_rent
from mcp_india_stack.tools.hra import calculate_hra_exemption
from mcp_india_stack.tools.income_tax import calculate_income_tax
from mcp_india_stack.tools.income_tax_interest import calculate_income_tax_interest
from mcp_india_stack.tools.leave_encashment import calculate_leave_encashment_tax
from mcp_india_stack.tools.nps_projection import calculate_nps_projection
from mcp_india_stack.tools.ppf_maturity import calculate_ppf_maturity
from mcp_india_stack.tools.presumptive_tax import calculate_presumptive_tax
from mcp_india_stack.tools.professional_tax import calculate_professional_tax
from mcp_india_stack.tools.rd_maturity import calculate_rd_maturity
from mcp_india_stack.tools.rules_metadata import (
    RULE_SETS,
    check_rules_staleness,
    get_rule_metadata,
)
from mcp_india_stack.tools.salary_restructuring import calculate_salary_restructuring
from mcp_india_stack.tools.sip_returns import calculate_sip_returns
from mcp_india_stack.tools.step_up_sip import calculate_step_up_sip
from mcp_india_stack.tools.sukanya_scss import calculate_sukanya_samriddhi
from mcp_india_stack.tools.surcharge import calculate_surcharge
from mcp_india_stack.tools.tds import calculate_tds


def test_rule_sets_registry_completeness() -> None:
    """Assert all 25 calculator rule sets are enumerated with complete metadata."""
    assert len(RULE_SETS) == 25
    for table_id, rule in RULE_SETS.items():
        assert rule.table_id == table_id
        assert rule.name
        assert rule.category in ("tax", "finance", "banking")
        assert rule.financial_year == "2025-26"
        assert "2025-26" in rule.supported_years
        assert rule.rules_version
        assert rule.effective_from.startswith("2025-")
        assert rule.effective_to >= "2026-03-31"
        assert rule.last_verified
        assert rule.source_ref.startswith("http")


def test_frozen_clock_staleness_logic() -> None:
    """Assert deterministic staleness detection with frozen dates."""
    # When frozen on verification date in Oct 2026: 0 issues
    fresh_date = date(2026, 10, 20)
    issues_fresh = check_rules_staleness(fresh_date)
    assert not issues_fresh, f"Expected 0 issues on {fresh_date}, got: {issues_fresh}"

    # When evaluated past effective_to (April 2027): reports expiry and stale verification
    future_date = date(2027, 4, 15)
    issues_future = check_rules_staleness(future_date)
    assert len(issues_future) > 0

    expired_issues = [i for i in issues_future if i["type"] == "expired"]
    stale_issues = [i for i in issues_future if i["type"] == "stale_verification"]
    assert len(expired_issues) == 25
    assert len(stale_issues) == 25


def test_unsupported_financial_year_handling() -> None:
    """Assert unsupported financial year returns structured error and never computes."""
    # Test on income tax
    bad_fy_res = calculate_income_tax(1_500_000, financial_year="1999-00")
    assert bad_fy_res.get("error") == "unsupported_financial_year"
    assert "supported_financial_years" in bad_fy_res
    assert "2025-26" in bad_fy_res["supported_financial_years"]
    assert "1999-00" in bad_fy_res["message"]

    # Test on TDS
    bad_tds = calculate_tds("194C_individual", 50000, True, financial_year="2020-21")
    assert bad_tds.get("error") == "unsupported_financial_year"
    assert "supported_financial_years" in bad_tds

    # Test on GST
    bad_gst = calculate_gst(10000, gst_rate=18.0, financial_year="2016-17")
    assert bad_gst.get("error") == "unsupported_financial_year"


def test_calculator_additive_provenance_fields_present() -> None:
    """Assert every calculator returns rules_version, effective_from, effective_to, source_ref."""
    calcs: list[tuple[str, dict[str, Any]]] = [
        ("income_tax", calculate_income_tax(1_000_000)),
        ("tds", calculate_tds("194J_professional", 50_000, True)),
        ("gst_calculator", calculate_gst(10_000, gst_rate=18.0)),
        ("surcharge", calculate_surcharge(6_000_000, 1_500_000, "new")),
        ("hra", calculate_hra_exemption(600_000, 240_000, 180_000, "metro")),
        ("capital_gains", calculate_capital_gains(200_000, 100_000, "equity", 400)),
        ("advance_tax", calculate_advance_tax(tax_liability=50_000)),
        ("gst_late_fee", calculate_gst_late_fee("GSTR3B", 10, 20_000_000)),
        ("income_tax_interest", calculate_income_tax_interest(100_000)),
        ("presumptive_tax", calculate_presumptive_tax("44ADA", 3_000_000)),
        ("professional_tax", calculate_professional_tax(50_000, "MH")),
        ("leave_encashment", calculate_leave_encashment_tax(500_000, 50_000, 60, 10)),
        ("salary_restructuring", calculate_salary_restructuring(1_200_000)),
        ("emi", calculate_emi(1_000_000, 8.5, 120)),
        ("gratuity", calculate_gratuity(80_000, 8.0)),
        ("ppf_maturity", calculate_ppf_maturity(100_000, 15)),
        ("fd_maturity", calculate_fd_maturity(500_000, annual_interest_rate=7.0, tenure_days=365)),
        ("rd_maturity", calculate_rd_maturity(10_000, 7.0, 24)),
        ("sip_returns", calculate_sip_returns(10_000, 12.0, 10)),
        ("step_up_sip", calculate_step_up_sip(10_000, 10.0, 12.0, 10)),
        ("nps_projection", calculate_nps_projection(10_000, 30, 60)),
        ("sukanya_samriddhi", calculate_sukanya_samriddhi("ssy", 100_000)),
        ("home_vs_rent", calculate_home_vs_rent(7_500_000)),
        ("epf_esic", calculate_epf_esic(20_000, 35_000)),
        ("neft_rtgs_imps_charges", calculate_neft_rtgs_imps_charges("NEFT", 50_000)),
    ]

    for table_id, result in calcs:
        meta = get_rule_metadata(table_id)
        assert result.get("rules_version") == meta.rules_version, (
            f"Missing rules_version in {table_id}"
        )
        assert result.get("effective_from") == meta.effective_from, (
            f"Missing effective_from in {table_id}"
        )
        assert result.get("effective_to") == meta.effective_to, (
            f"Missing effective_to in {table_id}"
        )
        assert result.get("source_ref") == meta.source_ref, f"Missing source_ref in {table_id}"
        assert result.get("financial_year") == "2025-26", f"Missing financial_year in {table_id}"


def test_golden_vector_tax_slabs_and_rebates() -> None:
    """Golden vectors for income tax: slabs, standard deduction, 87A rebate, and FY2026-27."""
    # Vector 1: Income of ₹12,00,000 under new regime has ₹75k standard deduction
    # Taxable = ₹11,25,000, which is below ₹12L, so 87A rebate makes total tax = 0
    v1 = calculate_income_tax(1_200_000, regime="new", financial_year="2025-26")
    assert v1["new_regime"]["total_tax"] == 0
    assert v1["new_regime"]["standard_deduction"] == 75_000

    # Vector 2: FY2026-27 calculation produces identical statutory result with AY 2027-28
    v2 = calculate_income_tax(1_200_000, regime="new", financial_year="2026-27")
    assert v2["new_regime"]["total_tax"] == 0
    assert v2["financial_year"] == "2026-27"
    assert v2["assessment_year"] == "2027-28"

    # Vector 3: Income of ₹15,00,000 under new regime
    # Standard deduction = 75,000 -> taxable = 14,25,000
    # 0-4L: 0
    # 4-8L: 20,000 (5% of 4L)
    # 8-12L: 40,000 (10% of 4L)
    # 12-14.25L: 33,750 (15% of 2.25L)
    # Base tax = 93,750. Cess = 4% of 93,750 = 3,750. Total = 97,500
    v3 = calculate_income_tax(1_500_000, regime="new")
    assert v3["new_regime"]["taxable_income"] == 1_425_000
    assert v3["new_regime"]["base_tax"] == 93_750.0
    assert v3["new_regime"]["cess"] == 3_750.0
    assert v3["new_regime"]["total_tax"] == 97_500.0


def test_golden_vector_surcharge_marginal_relief() -> None:
    """Golden vector for surcharge threshold crossing and marginal relief."""
    # Income ₹5,100,000 (just crossed ₹50L threshold) under new regime
    # Base tax on ₹5,100,000 without standard deduction
    base_tax = 1_110_000.0
    v_sur = calculate_surcharge(5_100_000, base_tax, "new")
    # Marginal relief should apply because excess income over 50L is 100,000
    assert v_sur["surcharge_rate"] == 0.10
    assert v_sur["surcharge_before_relief"] == 111_000.0
    assert v_sur["marginal_relief"] > 0
    assert v_sur["surcharge_after_relief"] < v_sur["surcharge_before_relief"]
