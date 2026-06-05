"""Tests for bulk aadhaar validation."""

from mcp_india_stack.tools.bulk_aadhaar import bulk_validate_aadhaar


class TestBulkAadhaarBasic:
    def test_single_valid(self):
        result = bulk_validate_aadhaar(numbers=["234123412340"])
        assert "results" in result
        assert len(result["results"]) == 1

    def test_multiple_valid(self):
        result = bulk_validate_aadhaar(numbers=["234123412340", "987654321012"])
        assert len(result["results"]) == 2

    def test_empty_list(self):
        result = bulk_validate_aadhaar(numbers=[])
        assert result.get("total") == 0

    def test_max_limit(self):
        # Should handle max 500
        numbers = [f"23412341234{i:02d}" for i in range(100)]
        result = bulk_validate_aadhaar(numbers=numbers)
        assert "results" in result

    def test_result_structure(self):
        result = bulk_validate_aadhaar(numbers=["234123412340"])
        r = result["results"][0]
        assert "valid" in r
        assert "index" in r


class TestBulkAadhaarMixed:
    def test_mixed_valid_invalid(self):
        result = bulk_validate_aadhaar(numbers=["234123412340", "invalid", "987654321012"])
        assert len(result["results"]) == 3

    def test_counts_correct(self):
        result = bulk_validate_aadhaar(numbers=["234123412340", "123456789012"])
        assert result.get("valid_count", 0) + result.get("invalid_count", 0) == len(
            result["results"]
        )
