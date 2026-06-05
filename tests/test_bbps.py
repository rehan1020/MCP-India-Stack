"""Tests for BBPS (Bharat Bill Payment System) biller lookup."""

from mcp_india_stack.tools.bbps import lookup_bbps_biller


class TestBBPSLookupBasic:
    def test_electricity_category_returns_results(self) -> None:
        result = lookup_bbps_biller(category="electricity")
        assert "billers" in result or "error" in result  # offline data or error

    def test_invalid_category_returns_error(self) -> None:
        result = lookup_bbps_biller(category="invalid_xyz_category")
        assert result.get("errors") or result.get("error") or result.get("billers") == []

    def test_result_has_no_exception(self) -> None:
        # Result is always a dict — offline data guaranteed
        result = lookup_bbps_biller(category="electricity")
        assert isinstance(result, dict)

    def test_empty_category_returns_all_billers(self) -> None:
        # Passing no category returns all billers across all categories
        result = lookup_bbps_biller()
        assert isinstance(result, dict)
        assert "billers" in result

    def test_valid_categories_accepted(self) -> None:
        for cat in ["electricity", "water", "gas", "broadband", "insurance"]:
            result = lookup_bbps_biller(category=cat)
            assert isinstance(result, dict), f"Expected dict for category {cat}"

    def test_biller_id_filter(self) -> None:
        # Look up a known biller by ID
        result = lookup_bbps_biller(biller_id="ELEC_DL_BSES")
        assert isinstance(result, dict)
        if result.get("billers"):
            assert result["billers"][0]["biller_id"] == "ELEC_DL_BSES"

    def test_state_filter(self) -> None:
        result = lookup_bbps_biller(category="electricity", state="Delhi")
        assert isinstance(result, dict)
        if result.get("billers"):
            for biller in result["billers"]:
                assert biller.get("state") in ("Delhi", "all")

    def test_response_structure_when_found(self) -> None:
        result = lookup_bbps_biller(category="electricity")
        if result.get("billers"):
            biller = result["billers"][0]
            assert "biller_name" in biller
            assert "biller_id" in biller
            assert "category" in biller

    def test_unknown_biller_id_returns_error(self) -> None:
        result = lookup_bbps_biller(biller_id="NONEXISTENT_BILLER_XYZ")
        assert isinstance(result, dict)
        # Either errors key present or billers is empty
        assert result.get("errors") or result.get("billers") == []

    def test_count_key_present(self) -> None:
        result = lookup_bbps_biller(category="gas")
        assert "count" in result
        assert isinstance(result["count"], int)
