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


class TestUpdateEdgeCases:
    def test_update_returns_http_404(self, tmp_cache: Path) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client = MagicMock()
        mock_get = MagicMock(return_value=mock_resp)
        mock_client.__enter__ = MagicMock(return_value=MagicMock(get=mock_get))
        mock_client.__exit__ = MagicMock(return_value=False)
        with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
            result = _fetch_and_cache("ifsc")
            assert result is False

    def test_update_returns_http_500(self, tmp_cache: Path) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_client = MagicMock()
        mock_get = MagicMock(return_value=mock_resp)
        mock_client.__enter__ = MagicMock(return_value=MagicMock(get=mock_get))
        mock_client.__exit__ = MagicMock(return_value=False)
        with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
            result = _fetch_and_cache("ifsc")
            assert result is False

    def test_corrupt_download_discarded_on_write(self, tmp_cache: Path) -> None:
        cached = tmp_cache / "IFSC.csv"
        cached.write_text("old_data")
        cached.read_text()

        with patch("mcp_india_stack.utils.updater._validate_csv", return_value=True):
            mock_resp = MagicMock()
            mock_resp.content = b"valid"
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_get = MagicMock(return_value=mock_resp)
            mock_client.__enter__ = MagicMock(return_value=MagicMock(get=mock_get))
            mock_client.__exit__ = MagicMock(return_value=False)
            with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
                with patch(
                    "mcp_india_stack.utils.updater.Path.write_bytes",
                    side_effect=OSError("disk full"),
                ):
                    result = _fetch_and_cache("ifsc")
                    assert result is False

    def test_force_refresh_handles_network_error(self, tmp_cache: Path) -> None:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(side_effect=ConnectionError("no network")))
        )
        mock_client.__exit__ = MagicMock(return_value=False)
        with patch("mcp_india_stack.utils.updater.httpx.Client", return_value=mock_client):
            result = _fetch_and_cache("ifsc")
            assert result is False

    def test_auto_update_disabled_returns_early(self, monkeypatch) -> None:
        from mcp_india_stack.utils import updater

        monkeypatch.setattr(updater, "_auto_update_disabled", lambda: True)
        with patch("mcp_india_stack.utils.updater._fetch_and_cache") as mock_fetch:
            updater.trigger_background_update("ifsc")
            mock_fetch.assert_not_called()

    def test_get_cache_info_exists(self, tmp_cache: Path) -> None:
        from mcp_india_stack.utils.updater import get_cache_info

        cached = tmp_cache / "IFSC.csv"
        cached.write_text("data")
        info = get_cache_info("ifsc")
        assert info["cached"] is True
        assert info["last_updated"] is not None

    def test_get_cache_info_not_exists(self, tmp_cache: Path) -> None:
        from mcp_india_stack.utils.updater import get_cache_info

        info = get_cache_info("ifsc")
        assert info["cached"] is False


class TestSupplyChainTrust:
    @pytest.fixture(autouse=True)
    def _reset_manifest_cache(self) -> None:
        from mcp_india_stack.utils import updater

        updater._checksum_manifest = None
        yield
        updater._checksum_manifest = None

    def test_all_datasets_in_manifest(self) -> None:
        """R1 Drift Guard: every DATASET_CONFIG key must be in the manifest."""
        import json

        from mcp_india_stack.utils.datasets import DATASET_CONFIG
        from mcp_india_stack.utils.updater import DATA_ROOT

        manifest_path = DATA_ROOT / "dataset_checksums.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name in DATASET_CONFIG:
            assert name in manifest, f"Dataset {name} missing from checksums manifest"
            assert "sha256" in manifest[name]

    def test_happy_path_verification(self, tmp_cache: Path) -> None:
        import hashlib

        from mcp_india_stack.utils import updater

        valid_data = b"col1,col2\nval1,val2\n"
        valid_hash = hashlib.sha256(valid_data).hexdigest()

        # Fake manifest
        updater._checksum_manifest = {"ifsc": {"sha256": valid_hash}}

        with patch("mcp_india_stack.utils.updater.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value.content = valid_data
            assert updater._fetch_and_cache("ifsc") is True
            assert (tmp_cache / "IFSC.csv").read_bytes() == valid_data

    def test_tampered_payload_verification(
        self, tmp_cache: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        from mcp_india_stack.utils import updater

        tampered_data = b"col1,col2\nevil,data\n"
        updater._checksum_manifest = {"ifsc": {"sha256": "expectedhash123"}}

        with patch("mcp_india_stack.utils.updater.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value.content = tampered_data

            with caplog.at_level(logging.ERROR):
                assert updater._fetch_and_cache("ifsc") is False
                assert not (tmp_cache / "IFSC.csv").exists()
                assert "Supply chain verification failed for ifsc" in caplog.text
                assert "Expected prefix: expected" in caplog.text
                assert "Fallback: bundled" in caplog.text

    def test_missing_manifest_entry(
        self, tmp_cache: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        from mcp_india_stack.utils import updater

        updater._checksum_manifest = {}

        with patch("mcp_india_stack.utils.updater.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value.content = b"col1\nval1"

            with caplog.at_level(logging.ERROR):
                assert updater._fetch_and_cache("ifsc") is False
                assert "not in manifest" in caplog.text

    def test_manifest_loaded_once(self) -> None:
        from mcp_india_stack.utils import updater

        with patch(
            "pathlib.Path.read_text", return_value='{"ifsc": {"sha256": "dummy"}}'
        ) as mock_read:
            with patch("mcp_india_stack.utils.updater.httpx.Client") as mock_client:
                mock_resp = mock_client.return_value.__enter__.return_value.get.return_value
                mock_resp.content = b"col1,col2\nval,val\n"
                updater._fetch_and_cache("ifsc")
                updater._fetch_and_cache("ifsc")
            mock_read.assert_called_once()
