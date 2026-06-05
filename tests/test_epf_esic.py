"""Tests for EPF/ESIC calculator."""

from mcp_india_stack.tools.epf_esic import calculate_epf_esic


class TestEPFESIC:
    def test_below_ceiling(self) -> None:
        result = calculate_epf_esic(basic_wages=12000, gross_wages=18000)
        assert result["epf"]["employee_epf_deduction"] == 1440
        assert result["esic"]["applicable"] is True

    def test_above_ceiling_esic_exempt(self) -> None:
        result = calculate_epf_esic(basic_wages=30000, gross_wages=45000)
        assert result["esic"]["applicable"] is False
        assert "exceeds ESIC ceiling" in result["esic"]["reason"]

    def test_eps_cap(self) -> None:
        result = calculate_epf_esic(basic_wages=20000, gross_wages=25000)
        assert result["epf"]["employer_eps"] == 1250

    def test_esic_boundary(self) -> None:
        result = calculate_epf_esic(basic_wages=15000, gross_wages=21000)
        assert result["esic"]["applicable"] is True

        result = calculate_epf_esic(basic_wages=15000, gross_wages=21001)
        assert result["esic"]["applicable"] is False

    def test_gross_less_than_basic_error(self) -> None:
        result = calculate_epf_esic(basic_wages=15000, gross_wages=10000)
        assert "errors" in result
        assert len(result["errors"]) > 0

    def test_negative_inputs(self) -> None:
        result = calculate_epf_esic(basic_wages=-1000, gross_wages=10000)
        assert "errors" in result
        assert len(result["errors"]) > 0


# ---- Bug 2 regression: EPF capped at wage ceiling ----


def test_epf_above_ceiling_statutory():
    """Statutory EPF: basic ₹30K → EPF on ₹15K ceiling = ₹1,800."""
    result = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000)
    assert result["epf"]["employee_epf_deduction"] == 1_800


def test_epf_above_ceiling_voluntary():
    """Voluntary PF: basic ₹30K → EPF on full ₹30K = ₹3,600."""
    result = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000, voluntary_pf_on_actual=True)
    assert result["epf"]["employee_epf_deduction"] == 3_600


def test_epf_below_ceiling():
    """Below ceiling: basic ₹12K → EPF = ₹1,440."""
    result = calculate_epf_esic(basic_wages=12_000, gross_wages=18_000)
    assert result["epf"]["employee_epf_deduction"] == 1_440


def test_epf_statutory_voluntary_fields():
    """Both statutory and voluntary amounts exposed."""
    result = calculate_epf_esic(basic_wages=30_000, gross_wages=50_000)
    assert result["epf"]["employee_epf_statutory"] == 1_800
    assert result["epf"]["employee_epf_voluntary"] == 3_600
