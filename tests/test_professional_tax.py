"""Tests for professional tax calculator."""

from mcp_india_stack.tools.professional_tax import calculate_professional_tax


def test_mh_above_10000():
    result = calculate_professional_tax(gross_salary_monthly=50000, state_code="MH")
    assert result.get("applicable") is True
    assert result.get("monthly_pt") > 0


def test_mh_between_7500_and_10000():
    result = calculate_professional_tax(gross_salary_monthly=8000, state_code="MH")
    assert result.get("applicable") is True
    assert result.get("monthly_pt") > 0


def test_mh_below_7500():
    result = calculate_professional_tax(gross_salary_monthly=500, state_code="MH")
    assert result.get("monthly_pt") == 0


def test_ka_above_30000():
    result = calculate_professional_tax(gross_salary_monthly=35000, state_code="KA")
    assert result.get("applicable") is True
    assert result.get("monthly_pt") > 0


def test_ka_below_15000():
    result = calculate_professional_tax(gross_salary_monthly=1000, state_code="KA")
    assert result.get("monthly_pt") == 0


def test_wb_slab():
    result = calculate_professional_tax(gross_salary_monthly=20000, state_code="WB")
    assert result.get("applicable") is True


def test_delhi_not_applicable():
    result = calculate_professional_tax(gross_salary_monthly=50000, state_code="DL")
    assert result.get("applicable") is False


def test_deductible_under_section_16():
    result = calculate_professional_tax(gross_salary_monthly=50000, state_code="MH")
    assert result.get("deductible_under_section_16") is True


def test_invalid_state_code():
    result = calculate_professional_tax(gross_salary_monthly=50000, state_code="XX")
    assert result.get("applicable") is False


def test_zero_salary():
    result = calculate_professional_tax(gross_salary_monthly=0, state_code="MH")
    assert result.get("monthly_pt") == 0


# --- Bug fix verification tests ---


def test_maharashtra_pt_25k():
    """Maharashtra ₹25K/month → monthly ₹200, Feb ₹300, annual ₹2,500."""
    result = calculate_professional_tax(25_000, "MH")
    assert result["monthly_pt"] == 200
    assert result["february_pt"] == 300
    assert result["annual_pt"] == 2_500  # was wrongly returning 300


def test_maharashtra_pt_8k():
    """Maharashtra ₹8K/month → monthly ₹175, no February spike in this slab."""
    result = calculate_professional_tax(8_000, "MH")
    assert result["monthly_pt"] == 175
    assert result["annual_pt"] == 175 * 12  # 2100


def test_delhi_no_pt():
    """Delhi has no professional tax."""
    result = calculate_professional_tax(1_00_000, "Delhi")
    assert result["annual_pt"] == 0
    assert result["applicable"] is False


def test_annual_tax_is_correct_for_ka():
    """Karnataka: ₹35K salary → ₹200/month × 12 = ₹2,400/year."""
    result = calculate_professional_tax(gross_salary_monthly=35000, state_code="KA")
    assert result["monthly_pt"] == 200
    assert result["annual_pt"] == 200 * 12  # 2400
