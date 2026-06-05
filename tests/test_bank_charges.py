"""Tests for bank transaction charges calculator."""

import pytest

from mcp_india_stack.tools.bank_charges import calculate_neft_rtgs_imps_charges


class TestNEFTCharges:
    def test_neft_online_savings_free(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=50000, account_type="savings", is_online=True
        )
        assert "errors" not in result
        assert result["total_charge"] == pytest.approx(0, abs=0.01)

    def test_neft_branch_below_10k(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=5000, account_type="savings", is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(2.50, abs=0.01)

    def test_neft_branch_10k_to_1l(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=50000, account_type="current", is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(5.0, abs=0.01)

    def test_neft_branch_1l_to_2l(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=150000, account_type="savings", is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(15.0, abs=0.01)

    def test_neft_branch_above_2l(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=300000, account_type="savings", is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(25.0, abs=0.01)

    def test_neft_online_current(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="NEFT", amount=50000, account_type="current", is_online=True
        )
        assert "errors" not in result
        assert result["base_charge"] > 0


class TestRTGSCharges:
    def test_rtgs_online_savings_free(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="RTGS", amount=500000, account_type="savings", is_online=True
        )
        assert "errors" not in result
        assert result["total_charge"] == pytest.approx(0, abs=0.01)

    def test_rtgs_below_minimum(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="RTGS", amount=100000)
        assert "errors" in result

    def test_rtgs_branch_2l_to_5l(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="RTGS", amount=300000, is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(25.0, abs=0.01)

    def test_rtgs_above_5l(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="RTGS", amount=600000, is_online=False
        )
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(50.0, abs=0.01)

    def test_rtgs_branch_online_current(self):
        result = calculate_neft_rtgs_imps_charges(
            transfer_mode="RTGS", amount=500000, account_type="current", is_online=True
        )
        assert "errors" not in result


class TestIMPSCharges:
    def test_imps_below_1000_free(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="IMPS", amount=500)
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(0, abs=0.01)

    def test_imps_1k_to_1l(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="IMPS", amount=50000)
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(5.0, abs=0.01)

    def test_imps_1l_to_2l(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="IMPS", amount=150000)
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(15.0, abs=0.01)

    def test_imps_above_2l(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="IMPS", amount=250000)
        assert "errors" not in result
        assert result["base_charge"] == pytest.approx(25.0, abs=0.01)

    def test_imps_gst_applied(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="IMPS", amount=50000)
        expected_gst = result["base_charge"] * 0.18
        assert result["gst_18pct"] == pytest.approx(expected_gst, abs=0.01)


class TestUPICharges:
    def test_upi_free(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="UPI", amount=1000)
        assert "errors" not in result
        assert result["total_charge"] == 0


class TestInvalidInputs:
    def test_invalid_mode(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="WIRE", amount=10000)
        assert "errors" in result

    def test_zero_amount(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="NEFT", amount=0)
        assert "errors" in result

    def test_negative_amount(self):
        result = calculate_neft_rtgs_imps_charges(transfer_mode="NEFT", amount=-1000)
        assert "errors" in result
