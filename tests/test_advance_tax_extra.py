from mcp_india_stack.tools.advance_tax import calculate_advance_tax


def test_advance_tax_invalid_inputs():
    r1 = calculate_advance_tax(tax_liability=-1000)
    assert r1["errors"]

    r2 = calculate_advance_tax(estimated_income=-1000)
    assert r2["errors"]


def test_advance_tax_fallback_regimes():
    r = calculate_advance_tax(estimated_income=50_00_000)
    assert r["total_tax_liability"] > 0
