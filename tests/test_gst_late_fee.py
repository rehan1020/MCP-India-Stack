"""Tests for GST late fee calculator."""

from mcp_india_stack.tools.gst_late_fee import calculate_gst_late_fee


class TestGSTR3B:
    def test_gstr3b_standard(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B", days_delayed=20, annual_turnover=20000000, has_nil_liability=False
        )
        assert "errors" not in result
        assert result["return_type"] == "GSTR3B"
        assert result["daily_fee"] == 50

    def test_gstr3b_nil_return(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B", days_delayed=20, annual_turnover=20000000, has_nil_liability=True
        )
        assert "errors" not in result
        assert result["daily_fee"] == 20  # Fixed: was 25, now correct ₹20

    def test_gstr3b_small_turnover_cap_2000(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B",
            days_delayed=200,
            annual_turnover=10000000,
            has_nil_liability=False,
        )
        assert result["total_late_fee"] <= 2000

    def test_gstr3b_medium_turnover_cap_5000(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B",
            days_delayed=200,
            annual_turnover=30000000,
            has_nil_liability=False,
        )
        assert result["total_late_fee"] <= 5000

    def test_gstr3b_large_turnover_cap_10000(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B",
            days_delayed=200,
            annual_turnover=100000000,
            has_nil_liability=False,
        )
        assert result["total_late_fee"] <= 10000


class TestGSTR1:
    def test_gstr1_standard(self):
        result = calculate_gst_late_fee(
            return_type="GSTR1", days_delayed=10, annual_turnover=10000000
        )
        assert "errors" not in result
        assert result["daily_fee"] == 50

    def test_gstr1_nil(self):
        result = calculate_gst_late_fee(
            return_type="GSTR1", days_delayed=10, annual_turnover=10000000, has_nil_liability=True
        )
        assert result["daily_fee"] == 20  # Fixed: was 25


class TestGSTR9:
    def test_gstr9_basic(self):
        result = calculate_gst_late_fee(
            return_type="GSTR9", days_delayed=10, annual_turnover=10000000
        )
        assert "errors" not in result
        assert result["daily_fee"] == 200
        assert result["total_late_fee"] == 2000

    def test_gstr9_cgst_sgst_split(self):
        result = calculate_gst_late_fee(
            return_type="GSTR9", days_delayed=10, annual_turnover=10000000
        )
        assert result["cgst_fee"] == result["sgst_fee"]


class TestZeroDelay:
    def test_zero_days_delayed(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B", days_delayed=0, annual_turnover=10000000
        )
        assert result["total_late_fee"] == 0


class TestInvalidInputs:
    def test_invalid_return_type(self):
        result = calculate_gst_late_fee(
            return_type="GSTR5", days_delayed=10, annual_turnover=10000000
        )
        assert "errors" in result

    def test_negative_days(self):
        result = calculate_gst_late_fee(
            return_type="GSTR3B", days_delayed=-5, annual_turnover=10000000
        )
        assert "errors" in result


# ---- Bug 5 regression: GSTR9 cap + nil rate ----


def test_gstr9_cap_enforced():
    """500 days late, turnover ₹20L → cap = ₹20L × 0.25% = ₹5,000."""
    result = calculate_gst_late_fee("GSTR9", 500, 20_00_000)
    # Cap = 20,00,000 × 0.25 / 100 = 5,000
    # Uncapped = 200 × 500 = 100,000
    assert result["total_late_fee"] == 5_000  # capped


def test_gstr9_cap_small_turnover():
    """GSTR9 cap on very small turnover."""
    result = calculate_gst_late_fee("GSTR9", 100, 2_00_000)
    # Cap = 2,00,000 × 0.25 / 100 = 500
    # Uncapped = 200 × 100 = 20,000
    assert result["total_late_fee"] == 500


def test_nil_return_fee_is_20_per_day():
    result = calculate_gst_late_fee("GSTR3B", 10, 50_00_000, has_nil_liability=True)
    assert result["daily_fee"] == 20
    assert result["total_late_fee"] == 200


def test_regular_return_fee_is_50_per_day():
    result = calculate_gst_late_fee("GSTR3B", 5, 50_00_000, has_nil_liability=False)
    assert result["daily_fee"] == 50
    assert result["total_late_fee"] == 250
