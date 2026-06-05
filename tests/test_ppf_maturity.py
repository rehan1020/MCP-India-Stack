"""Tests for PPF maturity calculator."""

from mcp_india_stack.tools.ppf_maturity import calculate_ppf_maturity


class TestPPFMaturity:
    def test_standard_15yr(self):
        result = calculate_ppf_maturity(annual_investment=100000, tenure_years=15)
        assert result["maturity_amount"] > 100000 * 15
        assert result["total_invested"] == 1500000

    def test_extended_20yr(self):
        result = calculate_ppf_maturity(annual_investment=100000, tenure_years=20)
        assert "maturity_amount" in result
        assert result["maturity_amount"] > 100000 * 20

    def test_min_investment(self):
        result = calculate_ppf_maturity(annual_investment=500, tenure_years=15)
        assert "errors" not in result

    def test_max_investment(self):
        result = calculate_ppf_maturity(annual_investment=150000, tenure_years=15)
        assert "errors" not in result

    def test_above_max_investment(self):
        result = calculate_ppf_maturity(annual_investment=160000, tenure_years=15)
        assert "errors" in result

    def test_invalid_tenure(self):
        result = calculate_ppf_maturity(annual_investment=100000, tenure_years=10)
        assert "errors" in result


class TestPPFBreakdown:
    def test_yearly_breakdown_present(self):
        result = calculate_ppf_maturity(annual_investment=100000, tenure_years=15)
        assert "yearly_breakdown" in result
        assert len(result["yearly_breakdown"]) == 15


class TestPPFRates:
    def test_custom_rate(self):
        result1 = calculate_ppf_maturity(
            annual_investment=100000, tenure_years=15, annual_interest_rate=8.0
        )
        result2 = calculate_ppf_maturity(
            annual_investment=100000, tenure_years=15, annual_interest_rate=7.0
        )
        assert result1["maturity_amount"] > result2["maturity_amount"]
