"""Tests for GST calculator."""

from mcp_india_stack.tools.gst_calculator import calculate_gst


def test_gst_hsn_code_professional_services():
    result = calculate_gst(amount=10000, hsn_code="9983")
    assert len(result.get("errors", [])) == 0
    assert result.get("gst_rate") == 18
    assert result.get("rate_source") == "hsn_lookup"


def test_gst_hsn_code_in_table():
    result = calculate_gst(amount=5000, hsn_code="9954")
    assert len(result.get("errors", [])) == 0


def test_gst_hsn_lookup_in_result():
    result = calculate_gst(amount=1000, hsn_code="9983")
    assert len(result.get("errors", [])) == 0
    assert "hsn_code_used" in result


def test_gst_neither_hsn_nor_rate():
    result = calculate_gst(amount=1000)
    assert len(result.get("errors", [])) > 0


def test_gst_hsn_not_in_table():
    result = calculate_gst(amount=1000, hsn_code="00000000")
    assert len(result.get("errors", [])) > 0


def test_gst_amount_inclusive_true():
    result = calculate_gst(amount=1180, gst_rate=18, amount_includes_gst=True)
    assert len(result.get("errors", [])) == 0
    assert result.get("base_amount") < 1180


def test_gst_inclusive_inter_state():
    result = calculate_gst(
        amount=1120, gst_rate=12, transaction_type="inter_state", amount_includes_gst=True
    )
    assert len(result.get("errors", [])) == 0


def test_gst_cess_applicable_flag():
    result = calculate_gst(amount=1000, gst_rate=28, cess_category="tobacco_cigarettes")
    assert len(result.get("errors", [])) == 0
    assert result.get("cess_rate", 0) > 0


def test_gst_invalid_transaction_type():
    result = calculate_gst(amount=1000, gst_rate=18, transaction_type="domestic")
    assert len(result.get("errors", [])) > 0


def test_gst_zero_amount():
    result = calculate_gst(amount=0, gst_rate=18)
    assert "errors" in result


def test_gst_negative_amount():
    result = calculate_gst(amount=-500, gst_rate=18)
    assert len(result.get("errors", [])) > 0
