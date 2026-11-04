"""Tests for G9: Bulk bounds, shared bounded executor, limits, and concurrency soak."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest

from mcp_india_stack.tools.bulk_common import (
    get_bulk_executor,
    get_bulk_max,
    get_bulk_payload_max,
)
from mcp_india_stack.tools.bulk_gstin import bulk_validate_gstin
from mcp_india_stack.tools.bulk_pan import bulk_validate_pan


def _is_valid(r: dict[str, Any]) -> bool:
    """Check validity supporting both flattened and unflattened item envelopes."""
    if r.get("valid") is True:
        return True
    if isinstance(r.get("data"), dict) and r["data"].get("valid") is True:
        return True
    return False


class TestBulkBoundsEnforcement:
    """Acceptance: 0, 1, max, max+1, duplicates, mixed, non-string, huge strings, homoglyphs."""

    def test_zero_items_rejected_before_work(self) -> None:
        res = bulk_validate_gstin([])
        assert res.get("success") is False
        assert "Empty GSTIN list" in res.get("errors", [])[0]

        res_pan = bulk_validate_pan([])
        assert res_pan.get("success") is False
        assert len(res_pan.get("errors", [])) > 0

    def test_single_item(self) -> None:
        res = bulk_validate_gstin(["27AAPFU0939F1ZV"])
        assert res.get("success") is True
        data = res.get("data", {})
        assert data.get("total") == 1
        assert len(data.get("results", [])) == 1
        assert _is_valid(data["results"][0])

    def test_max_items_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_INDIA_STACK_BULK_MAX", "25")
        assert get_bulk_max() == 25

        items = ["27AAPFU0939F1ZV"] * 25
        res = bulk_validate_gstin(items)
        assert res.get("success") is True
        assert res["data"]["total"] == 25
        assert len(res["data"]["results"]) == 25

    def test_max_plus_one_rejected_before_work(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_INDIA_STACK_BULK_MAX", "20")
        assert get_bulk_max() == 20

        items = ["27AAPFU0939F1ZV"] * 21
        res = bulk_validate_gstin(items)
        assert res.get("success") is False
        assert "Maximum 20" in res.get("errors", [])[0]
        assert "got 21" in res.get("errors", [])[0]

    def test_duplicates_order_preserved(self) -> None:
        items = ["27AAPFU0939F1ZV", "INVALID123", "27AAPFU0939F1ZV", "INVALID456"]
        res = bulk_validate_gstin(items)
        assert res.get("success") is True
        results = res["data"]["results"]
        assert len(results) == 4
        assert _is_valid(results[0])
        assert not _is_valid(results[1])
        assert _is_valid(results[2])
        assert not _is_valid(results[3])

    def test_mixed_valid_invalid_isolation(self) -> None:
        items = [
            "27AAPFU0939F1ZV",
            "INVALID_GSTIN_1",
            "36AAACB9999P1Z1",
            "99ZZZZZ0000Z0Z0",
        ]
        res = bulk_validate_gstin(items)
        assert res.get("success") is True
        data = res["data"]
        assert data["total"] == 4
        assert len(data["results"]) == 4
        assert _is_valid(data["results"][0])
        assert not _is_valid(data["results"][1])

    def test_non_string_items_isolated(self) -> None:
        items = ["27AAPFU0939F1ZV", None, 12345, "27AAPFU0939F1ZV"]  # type: ignore[list-item]
        res = bulk_validate_gstin(items)
        assert res.get("success") is True
        results = res["data"]["results"]
        assert len(results) == 4
        assert _is_valid(results[0])
        assert not _is_valid(results[1])
        assert "Invalid GSTIN format" in results[1]["errors"][0]
        assert not _is_valid(results[2])
        assert "Invalid GSTIN format" in results[2]["errors"][0]
        assert _is_valid(results[3])

    def test_huge_strings_isolated_or_capped(self) -> None:
        # Single item exceeding item max len (e.g. 1000 chars) is isolated with error
        huge_item = "X" * 1000
        res = bulk_validate_gstin(["27AAPFU0939F1ZV", huge_item])
        assert res.get("success") is True
        results = res["data"]["results"]
        assert _is_valid(results[0])
        assert not _is_valid(results[1])
        assert "Item exceeds maximum length" in results[1]["errors"][0]

    def test_total_payload_cap_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_INDIA_STACK_BULK_PAYLOAD_MAX", "500")
        assert get_bulk_payload_max() == 500

        # Create payload > 500 bytes
        items = ["27AAPFU0939F1ZV"] * 50  # 15 * 50 = 750 bytes
        res = bulk_validate_gstin(items)
        assert res.get("success") is False
        assert "exceeds limit" in res.get("errors", [])[0]

    def test_unicode_and_homoglyphs(self) -> None:
        # Cyrillic А (U+0410) instead of Latin A
        cyrillic_homoglyph = "27\u0410\u0410PFU0939F1ZV"
        res = bulk_validate_gstin(["27AAPFU0939F1ZV", cyrillic_homoglyph])
        assert res.get("success") is True
        results = res["data"]["results"]
        assert _is_valid(results[0])
        assert not _is_valid(results[1])


class TestConcurrencySoak:
    """50 concurrent calls with one shared bounded executor and no deadlock."""

    def test_50_concurrent_calls_no_deadlock(self) -> None:
        call_count = 50
        batches = [
            ["27AAPFU0939F1ZV", "INVALID_TEST", "27AAPFU0939F1ZV"] for _ in range(call_count)
        ]

        def _make_call(batch: list[str]) -> dict[str, Any]:
            return bulk_validate_gstin(batch)

        with ThreadPoolExecutor(max_workers=25) as client_pool:
            futures = [client_pool.submit(_make_call, b) for b in batches]
            completed = 0
            for fut in as_completed(futures, timeout=20.0):
                res = fut.result()
                assert res.get("success") is True
                assert res["data"]["total"] == 3
                assert len(res["data"]["results"]) == 3
                completed += 1

        assert completed == call_count

    def test_shared_executor_is_singleton(self) -> None:
        exec1 = get_bulk_executor()
        exec2 = get_bulk_executor()
        assert exec1 is exec2
