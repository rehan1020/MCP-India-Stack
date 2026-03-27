"""Tests for GST calculator."""

from mcp_india_stack.tools.gst_calculator import calculate_gst


class TestAllRates:
    def test_zero_rate(self) -> None:
        result = calculate_gst(1000, 0, "intra_state")
        assert result["total_gst"] == 0
        assert result["total_amount"] == 1000

    def test_5_percent_intra(self) -> None:
        result = calculate_gst(1000, 5, "intra_state")
        assert result["cgst_amount"] == 25.0
        assert result["sgst_amount"] == 25.0
        assert result["igst_amount"] == 0
        assert result["total_gst"] == 50.0

    def test_5_percent_inter(self) -> None:
        result = calculate_gst(1000, 5, "inter_state")
        assert result["igst_amount"] == 50.0
        assert result["cgst_amount"] == 0
        assert result["sgst_amount"] == 0

    def test_12_percent(self) -> None:
        result = calculate_gst(10000, 12, "intra_state")
        assert result["cgst_amount"] == 600.0
        assert result["sgst_amount"] == 600.0

    def test_18_percent(self) -> None:
        result = calculate_gst(10000, 18, "inter_state")
        assert result["igst_amount"] == 1800.0

    def test_28_percent(self) -> None:
        result = calculate_gst(10000, 28, "intra_state")
        assert result["total_gst"] == 2800.0

    def test_0_1_percent(self) -> None:
        result = calculate_gst(100000, 0.1, "inter_state")
        assert result["igst_amount"] == 100.0

    def test_0_25_percent(self) -> None:
        result = calculate_gst(100000, 0.25, "inter_state")
        assert result["igst_amount"] == 250.0

    def test_1_5_percent(self) -> None:
        result = calculate_gst(100000, 1.5, "inter_state")
        assert result["igst_amount"] == 1500.0

    def test_3_percent(self) -> None:
        result = calculate_gst(100000, 3, "inter_state")
        assert result["igst_amount"] == 3000.0


class TestInclusive:
    def test_gst_inclusive_18(self) -> None:
        """Back-calculate base from GST-inclusive amount."""
        result = calculate_gst(1180, 18, "intra_state", amount_includes_gst=True)
        assert result["base_amount"] == 1000.0
        assert result["total_amount"] == 1180.0


class TestInvalidRate:
    def test_invalid_rate(self) -> None:
        result = calculate_gst(1000, 15, "intra_state")
        assert len(result["errors"]) > 0
        assert "Invalid GST rate" in result["errors"][0]


class TestCess:
    def test_28_with_cess(self) -> None:
        result = calculate_gst(10000, 28, "intra_state", cess_category="aerated_drinks")
        assert result["cess_amount"] == 1200.0
        assert result["cess_rate"] == 12.0


class TestDisclaimer:
    def test_disclaimer_present(self) -> None:
        result = calculate_gst(1000, 18, "intra_state")
        assert "disclaimer" in result
