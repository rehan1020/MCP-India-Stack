"""Tests for TDS calculator."""

from mcp_india_stack.tools.tds import calculate_tds


class TestBelowThreshold:
    def test_194C_below_threshold(self) -> None:
        result = calculate_tds("194C_individual", 20_000, pan_available=True)
        assert result["tds_applicable"] is False
        assert result["tds_amount"] == 0
        assert result["net_payment"] == 20_000

    def test_194H_below_threshold(self) -> None:
        result = calculate_tds("194H", 10_000, pan_available=True)
        assert result["tds_applicable"] is False


class TestWithPAN:
    def test_194C_individual_with_pan(self) -> None:
        result = calculate_tds("194C_individual", 50_000, pan_available=True)
        assert result["tds_applicable"] is True
        assert result["rate_applied"] == 0.01
        assert result["tds_amount"] == 500.0

    def test_194J_professional(self) -> None:
        result = calculate_tds("194J_professional", 100_000, pan_available=True)
        assert result["rate_applied"] == 0.10
        assert result["tds_amount"] == 10_000.0

    def test_194I_land(self) -> None:
        result = calculate_tds("194I_land", 300_000, pan_available=True)
        assert result["rate_applied"] == 0.10
        assert result["tds_amount"] == 30_000.0

    def test_194Q_purchase(self) -> None:
        result = calculate_tds("194Q", 6_000_000, pan_available=True)
        assert result["rate_applied"] == 0.001
        assert result["tds_amount"] == 6_000.0


class TestWithoutPAN:
    def test_194C_without_pan_higher_rate(self) -> None:
        result = calculate_tds("194C_individual", 50_000, pan_available=False)
        assert result["rate_applied"] == 0.20
        assert result["tds_amount"] == 10_000.0
        assert result["no_pan_surcharge"] > 0

    def test_194A_other_without_pan(self) -> None:
        result = calculate_tds("194A_other", 10_000, pan_available=False)
        assert result["rate_applied"] == 0.20


class TestSeniorCitizen194A:
    def test_senior_bank_interest_50k_threshold(self) -> None:
        """Senior citizen 194A bank threshold is ₹50,000 not ₹40,000."""
        result = calculate_tds(
            "194A_bank", 45_000, pan_available=True, is_senior_citizen=True
        )
        assert result["tds_applicable"] is False  # Below ₹50K threshold

    def test_non_senior_bank_interest_40k_threshold(self) -> None:
        """Non-senior 194A bank threshold is ₹40,000."""
        result = calculate_tds(
            "194A_bank", 45_000, pan_available=True, is_senior_citizen=False
        )
        assert result["tds_applicable"] is True  # Above ₹40K threshold


class TestAllMajorSections:
    def test_194C_company(self) -> None:
        result = calculate_tds("194C_company", 50_000, pan_available=True)
        assert result["rate_applied"] == 0.02

    def test_194J_technical(self) -> None:
        result = calculate_tds("194J_technical", 50_000, pan_available=True)
        assert result["rate_applied"] == 0.02

    def test_194A_bank(self) -> None:
        result = calculate_tds("194A_bank", 50_000, pan_available=True)
        assert result["rate_applied"] == 0.10

    def test_194H(self) -> None:
        result = calculate_tds("194H", 20_000, pan_available=True)
        assert result["rate_applied"] == 0.05

    def test_194I_plant(self) -> None:
        result = calculate_tds("194I_plant", 300_000, pan_available=True)
        assert result["rate_applied"] == 0.02

    def test_194B_lottery(self) -> None:
        result = calculate_tds("194B", 50_000, pan_available=True)
        assert result["rate_applied"] == 0.30

    def test_194D_insurance(self) -> None:
        result = calculate_tds("194D", 20_000, pan_available=True)
        assert result["rate_applied"] == 0.05


class TestInvalidSection:
    def test_unknown_section(self) -> None:
        result = calculate_tds("INVALID", 50_000, pan_available=True)
        assert len(result["errors"]) > 0


class TestFinancialYear:
    def test_fy_present(self) -> None:
        result = calculate_tds("194C_individual", 50_000, pan_available=True)
        assert result["financial_year"] == "2025-26"
