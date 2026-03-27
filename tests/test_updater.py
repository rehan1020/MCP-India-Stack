"""Tests for the dataset updater module."""

from __future__ import annotations

import gzip
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_india_stack.utils.updater import (
    _bundled_path,
    _fetch_and_cache,
    _is_stale,
    _validate_csv,
    _validate_gzip,
    force_refresh_all,
    get_dataset_path,
    trigger_background_update,
)

# --- Fixtures ---


@pytest.fixture()
def tmp_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect cache dir to a temp directory for tests."""
    monkeypatch.setattr(
        "mcp_india_stack.utils.updater.get_cache_dir",
        lambda: tmp_path,
    )
    return tmp_path


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure MCP_INDIA_STACK_NO_AUTO_UPDATE is not set during tests."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)


# --- Unit tests ---


class TestValidation:
    def test_validate_csv_valid(self) -> None:
        data = b"col1,col2\nval1,val2\n"
        assert _validate_csv(data) is True

    def test_validate_csv_empty(self) -> None:
        assert _validate_csv(b"") is False

    def test_validate_csv_garbage(self) -> None:
        # Invalid UTF-8 continuation bytes that cannot be decoded
        assert _validate_csv(b"\x80\x81\x82") is False

    def test_validate_gzip_valid(self) -> None:
        import io

        buf = io.BytesIO()
        with gzip.open(buf, "wt", encoding="utf-8") as fh:
            fh.write("col1,col2\nval1,val2\n")
        assert _validate_gzip(buf.getvalue()) is True

    def test_validate_gzip_garbage(self) -> None:
        assert _validate_gzip(b"not gzip data") is False


class TestStaleness:
    def test_missing_file_is_stale(self, tmp_path: Path) -> None:
        assert _is_stale(tmp_path / "nonexistent.csv", 30) is True

    def test_fresh_file_is_not_stale(self, tmp_path: Path) -> None:
        f = tmp_path / "fresh.csv"
        f.write_text("data")
        assert _is_stale(f, 30) is False

    def test_old_file_is_stale(self, tmp_path: Path) -> None:
        f = tmp_path / "old.csv"
        f.write_text("data")
        # Set mtime to 60 days ago
        old_time = time.time() - (60 * 86400)
        os.utime(f, (old_time, old_time))
        assert _is_stale(f, 30) is True


class TestGetDatasetPath:
    def test_returns_bundled_when_no_cache(self, tmp_cache: Path) -> None:
        """When no cache exists, return the bundled path."""
        with patch("mcp_india_stack.utils.updater.trigger_background_update") as mock_trigger:
            result = get_dataset_path("ifsc")
            assert result == _bundled_path("ifsc")
            mock_trigger.assert_called_once_with("ifsc")

    def test_returns_cached_when_fresh(self, tmp_cache: Path) -> None:
        """When a fresh cache exists, return the cached path."""
        cached = tmp_cache / "IFSC.csv"
        cached.write_text("BANK,IFSC\nHDFC,HDFC0000001\n")
        with patch("mcp_india_stack.utils.updater.trigger_background_update") as mock_trigger:
            result = get_dataset_path("ifsc")
            assert result == cached
            mock_trigger.assert_not_called()

    def test_returns_cached_but_triggers_update_when_stale(self, tmp_cache: Path) -> None:
        """When cache is stale, return it but trigger background update."""
        cached = tmp_cache / "IFSC.csv"
        cached.write_text("BANK,IFSC\nHDFC,HDFC0000001\n")
        old_time = time.time() - (60 * 86400)
        os.utime(cached, (old_time, old_time))
        with patch("mcp_india_stack.utils.updater.trigger_background_update") as mock_trigger:
            result = get_dataset_path("ifsc")
            assert result == cached
            mock_trigger.assert_called_once_with("ifsc")

    def test_unknown_dataset_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown dataset"):
            get_dataset_path("nonexistent")


class TestBackgroundUpdate:
    def test_does_not_block(self, tmp_cache: Path) -> None:
        """trigger_background_update returns immediately."""
        import time as t

        with patch("mcp_india_stack.utils.updater._fetch_and_cache") as mock_fetch:
            mock_fetch.side_effect = lambda _: t.sleep(5)
            start = t.time()
            trigger_background_update("ifsc")
            elapsed = t.time() - start
            assert elapsed < 1.0  # Should return near-instantly


class TestEnvVarOptOut:
    def test_no_auto_update_disables_background(
        self, tmp_cache: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_INDIA_STACK_NO_AUTO_UPDATE disables all update attempts."""
        monkeypatch.setenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", "1")
        with patch("mcp_india_stack.utils.updater._fetch_and_cache") as mock_fetch:
            # Should return bundled path without triggering any update
            result = get_dataset_path("ifsc")
            assert result == _bundled_path("ifsc")
            mock_fetch.assert_not_called()


class TestCorruptDownload:
    def test_corrupt_file_is_discarded(self, tmp_cache: Path) -> None:
        """If validation fails after download, keep old cache."""
        cached = tmp_cache / "IFSC.csv"
        cached.write_text("BANK,IFSC\nold_data\n")

        # Mock httpx to return data, but mock validation to fail
        with patch("mcp_india_stack.utils.updater._validate_csv", return_value=False):
            mock_resp = MagicMock()
            mock_resp.content = b"corrupt data"
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_get = MagicMock(return_value=mock_resp)
            mock_client.__enter__ = MagicMock(return_value=MagicMock(get=mock_get))
            mock_client.__exit__ = MagicMock(return_value=False)
            with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
                result = _fetch_and_cache("ifsc")
                assert result is False
                # Old file should still be there
                assert cached.read_text() == "BANK,IFSC\nold_data\n"


class TestNetworkTimeout:
    def test_timeout_handled_gracefully(self, tmp_cache: Path) -> None:
        """Network timeout does not raise an exception."""
        import httpx

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(side_effect=httpx.TimeoutException("timeout")))
        )
        mock_client.__exit__ = MagicMock(return_value=False)
        with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
            result = _fetch_and_cache("ifsc")
            assert result is False  # No exception raised


class TestForceRefresh:
    def test_force_refresh_returns_results(self, tmp_cache: Path) -> None:
        """force_refresh_all returns dict with success status for each dataset."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(side_effect=Exception("network error")))
        )
        mock_client.__exit__ = MagicMock(return_value=False)
        with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
            results = force_refresh_all()
            assert isinstance(results, dict)
            assert all(v is False for v in results.values())
            assert set(results.keys()) == {"ifsc", "pincode", "hsn"}
