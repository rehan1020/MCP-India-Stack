"""Tests for presumptive tax calculator."""

import pytest

from mcp_india_stack.tools.presumptive_tax import _compute_slab_tax, calculate_presumptive_tax


class Test44ADHappyPath:
    def test_44ad_basic(self):
        result = calculate_presumptive_tax(scheme="44AD", gross_receipts=1000000)
        assert "errors" not in result
        assert result["scheme"] == "44AD"
        assert result["gross_receipts"] == 1000000

    def test_44ad_full_digital_95plus(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2500000, digital_receipt_percent=100
        )
        assert "errors" not in result
        assert result["presumptive_income"] == 150000

    def test_44ad_below_95_digital(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=1800000, digital_receipt_percent=50
        )
        assert "errors" not in result
        assert result["presumptive_income"] == 126000

    def test_44ad_at_3cr_digital_threshold(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=3_00_00_000, digital_receipt_percent=100
        )
        assert "errors" not in result

    def test_44ad_at_2cr_cash_threshold(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2_00_00_000, digital_receipt_percent=50
        )
        assert "errors" not in result


class Test44ADInvalidInputs:
    def test_44ad_above_3cr_digital_ineligible(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=3_50_00_000, digital_receipt_percent=100
        )
        assert "errors" in result
        assert "3" in result["errors"][0]

    def test_44ad_above_2cr_cash_ineligible(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2_50_00_000, digital_receipt_percent=50
        )
        assert "errors" in result


class Test44ADAHappyPath:
    def test_44ada_basic(self):
        result = calculate_presumptive_tax(scheme="44ADA", gross_receipts=400000)
        assert "errors" not in result
        assert result["scheme"] == "44ADA"

    def test_44ada_50pct_income(self):
        result = calculate_presumptive_tax(scheme="44ADA", gross_receipts=500000)
        assert "errors" not in result
        assert result["presumptive_income"] == 250000
        assert result["presumptive_rate"] == "50%"

    def test_44ada_new_regime_tax(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=500000, digital_receipt_percent=100, regime="new"
        )
        assert "errors" not in result
        assert "total_tax_payable" in result


class Test44ADAInvalidInputs:
    def test_44ada_above_75l_digital_ineligible(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=80_00_000, digital_receipt_percent=100
        )
        assert "errors" in result
        assert "75" in result["errors"][0]

    def test_44ada_above_50l_cash_ineligible(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=60_00_000, digital_receipt_percent=50
        )
        assert "errors" in result


class TestInvalidScheme:
    def test_invalid_scheme(self):
        result = calculate_presumptive_tax(scheme="44AB", gross_receipts=100000)
        assert "errors" in result

    def test_zero_receipts(self):
        result = calculate_presumptive_tax(scheme="44AD", gross_receipts=0)
        assert "errors" in result

    def test_negative_receipts(self):
        result = calculate_presumptive_tax(scheme="44AD", gross_receipts=-1000)
        assert "errors" in result


class TestOldRegime:
    def test_44ad_old_regime_with_deductions(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=1000000, regime="old", deductions_80c=100000
        )
        assert "errors" not in result

    def test_44ada_old_regime_tax(self):
        result = calculate_presumptive_tax(scheme="44ADA", gross_receipts=400000, regime="old")
        assert "errors" not in result


class TestEdgeCases:
    def test_44ad_zero_digital(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=1500000, digital_receipt_percent=0
        )
        assert "errors" not in result

    def test_44ada_at_50l_cash_threshold(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=50_00_000, digital_receipt_percent=50
        )
        assert "errors" not in result


class TestDigitalThreshold:
    def test_44ad_below_3cr_less_than_95pct_digital(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2_50_00_000, digital_receipt_percent=50
        )
        assert "errors" in result

    def test_44ad_exactly_at_2cr_limit_non_digital(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2_00_00_000, digital_receipt_percent=50
        )
        assert "errors" not in result

    def test_44ada_below_75l_less_than_95pct_digital(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=60_00_000, digital_receipt_percent=50
        )
        assert "errors" in result

    def test_44ada_at_50l_non_digital(self):
        result = calculate_presumptive_tax(
            scheme="44ADA", gross_receipts=50_00_000, digital_receipt_percent=50
        )
        assert "errors" not in result


class TestOldRegimeTaxBrackets:
    def test_44ad_old_regime_above_8_lakh(self):
        result = calculate_presumptive_tax(
            scheme="44AD",
            gross_receipts=2_00_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert "errors" not in result
        assert result["total_tax_payable"] > 0

    def test_44ad_old_regime_above_16_lakh(self):
        result = calculate_presumptive_tax(
            scheme="44AD",
            gross_receipts=3_00_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert "errors" not in result
        assert result["total_tax_payable"] > 0

    def test_44ad_old_regime_5_percent_bracket(self):
        result = calculate_presumptive_tax(
            scheme="44AD",
            gross_receipts=1_00_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert "errors" not in result
        assert result["total_tax_payable"] > 0

    def test_44ad_old_regime_15_percent_bracket(self):
        result = calculate_presumptive_tax(
            scheme="44AD",
            gross_receipts=2_50_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert "errors" not in result
        assert result["total_tax_payable"] > 0

    def test_44ad_old_regime_30_percent_bracket(self):
        """Old regime: taxable >10L -> 30% bracket."""
        result = calculate_presumptive_tax(
            scheme="44ADA",
            gross_receipts=50_00_000,
            digital_receipt_percent=100,
            regime="old",
            deductions_80c=0,
        )
        assert "errors" not in result
        assert result["total_tax_payable"] > 0


class TestNewRegimeTaxBrackets:
    def test_44ad_new_regime_above_8_lakh(self):
        result = calculate_presumptive_tax(
            scheme="44AD", gross_receipts=2_00_00_000, digital_receipt_percent=100, regime="new"
        )
        assert "errors" not in result


# --- Bug fix verification tests ---


def test_44ad_80_lakh_digital_eligible():
    result = calculate_presumptive_tax("44AD", 80_00_000, digital_receipt_percent=80)
    assert "errors" not in result or result.get("errors") == []
    assert result["presumptive_income"] > 0


def test_44ada_45_lakh_eligible():
    result = calculate_presumptive_tax("44ADA", 45_00_000, digital_receipt_percent=100)
    assert "errors" not in result or result.get("errors") == []
    assert result["presumptive_income"] == pytest.approx(45_00_000 * 0.5)


def test_44ad_above_3cr_ineligible():
    result = calculate_presumptive_tax("44AD", 3_50_00_000)
    assert result["errors"]
    assert "3" in result["errors"][0]


def test_44ada_above_75l_ineligible():
    result = calculate_presumptive_tax("44ADA", 80_00_000)
    assert result["errors"]
    assert "75" in result["errors"][0]


# ---- Bug 4 regression: full slab coverage ----


def test_44ada_45l_new_regime_tax():
    """₹45L receipts → presumptive ₹22.5L, SD ₹75K, taxable ₹21.75L → hits high slabs."""
    result = calculate_presumptive_tax(
        "44ADA", 45_00_000, digital_receipt_percent=100, regime="new"
    )
    # Tax before cess should be ~₹2,43,750
    assert 2_40_000 < result["tax_after_cess"] < 2_60_000


def test_44ad_new_regime_high_income():
    """₹2Cr receipts → presumptive ₹12L (6%), taxable ~₹11.25L → should hit higher slabs."""
    result = calculate_presumptive_tax(
        "44AD", 2_00_00_000, digital_receipt_percent=100, regime="new"
    )
    # Presumptive = ₹12L, taxable = ₹12L - ₹75K = ₹11.25L
    # With 87A rebate (taxable ≤ 12L): tax = 0 — actually taxable = 11.25L ≤ 12L → rebate!
    assert result["tax_after_cess"] == 0  # 87A rebate applies


def test_44ada_60l_new_regime_hits_25pct_slab():
    """₹60L receipts → presumptive ₹30L → should hit 25%+ slab."""
    result = calculate_presumptive_tax(
        "44ADA", 60_00_000, digital_receipt_percent=100, regime="new"
    )
    # Presumptive = ₹30L, taxable = ₹30L - ₹75K = ₹29.25L → 30% slab
    assert result["tax_after_cess"] > 4_00_000


def test_compute_slab_tax_new_regime():
    """Unit test for _compute_slab_tax helper."""
    from mcp_india_stack.tools.presumptive_tax import NEW_REGIME_SLABS

    # Taxable = ₹21.75L
    tax = _compute_slab_tax(21_75_000, NEW_REGIME_SLABS)
    # 0-4L: 0, 4-8L: 20K, 8-12L: 40K, 12-16L: 60K, 16-20L: 80K, 20-21.75L: 43750
    expected = 0 + 20_000 + 40_000 + 60_000 + 80_000 + 43_750
    assert tax == pytest.approx(expected, abs=1)
