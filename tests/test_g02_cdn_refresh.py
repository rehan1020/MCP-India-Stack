"""Tests for G2: Hardened CDN refresh pipeline."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

import pytest

from mcp_india_stack.network.cdn_refresh import (
    CdnRefreshError,
    refresh_dataset,
)
from mcp_india_stack.server import server_status


def test_g2_status_exposes_last_refresh_error() -> None:
    """india://status additively exposes last_refresh_error."""
    status = server_status()
    assert "last_refresh_error" in status
    assert status["last_refresh_error"] is None or isinstance(status["last_refresh_error"], str)


def test_g2_opt_out_env_produces_zero_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """MCP_INDIA_STACK_NO_AUTO_UPDATE=1 produces zero network calls."""
    monkeypatch.setenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", "1")

    def fail_on_connect(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Network socket called when auto-update disabled")

    monkeypatch.setattr(socket.socket, "connect", fail_on_connect)
    res = refresh_dataset("ifsc")
    assert res is False


def test_g2_rejects_http_downgrade(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects non-HTTPS schemes or HTTP downgrade redirects."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    with pytest.raises(CdnRefreshError, match="HTTPS"):
        refresh_dataset("ifsc", url_override="http://cdn.jsdelivr.net/test.csv")


def test_g2_rejects_unlisted_host(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects URLs from hosts not on the allowlist."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    with pytest.raises(CdnRefreshError, match="allowlist"):
        refresh_dataset("ifsc", url_override="https://evil.example.com/IFSC.csv")


def test_g2_rejects_cross_host_redirect(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects cross-host redirects even if target is https."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    # Simulated redirect across hosts
    with pytest.raises(CdnRefreshError, match="cross-host"):
        refresh_dataset(
            "ifsc",
            mock_redirect_chain=[
                "https://cdn.jsdelivr.net/IFSC.csv",
                "https://other-domain.com/IFSC.csv",
            ],
        )


def test_g2_rejects_oversized_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects downloads exceeding the download size cap."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    with pytest.raises(CdnRefreshError, match="oversized|size cap"):
        refresh_dataset("ifsc", mock_payload=b"A" * (51 * 1024 * 1024))  # 51MB > 50MB cap


def test_g2_rejects_decompression_bomb(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects gzip downloads where uncompressed data exceeds decompression cap."""
    import gzip

    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    # 1MB of zeroes compresses into ~1KB gzip, but decompressed exceeds bomb limit if large
    bomb_compressed = gzip.compress(b"0" * (105 * 1024 * 1024))  # 105MB uncompressed
    with pytest.raises(CdnRefreshError, match="(?i)decompression"):
        refresh_dataset("pincode", mock_payload=bomb_compressed)


def test_g2_rejects_truncated_or_invalid_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Rejects payloads with invalid schema/headers."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    with pytest.raises(CdnRefreshError, match="schema|truncated"):
        refresh_dataset("ifsc", mock_payload=b"bad,header\n1,2\n")


def test_g2_rejects_older_version_rollback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Rejects older version rollbacks when cached version is newer."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    cache_file = tmp_path / "IFSC.csv"
    cache_file.write_text(
        "BANK,IFSC,BRANCH,CENTRE,DISTRICT,STATE,ADDRESS,CONTACT,UPI,RTGS,CITY,NEFT,IMPS,MICR\n"
        "v2,IFSC001,Main,Centre,Dist,State,Addr,123,true,true,City,true,true,123\n",
        encoding="utf-8",
    )
    with pytest.raises(CdnRefreshError, match="rollback|older version"):
        refresh_dataset(
            "ifsc",
            mock_payload=(
                b"BANK,IFSC,BRANCH,CENTRE,DISTRICT,STATE,ADDRESS,CONTACT,UPI,RTGS,CITY,NEFT,IMPS,MICR\n"
                b"v1,IFSC001,Main,Centre,Dist,State,Addr,123,true,true,City,true,true,123\n"
            ),
            mock_version=1,
            current_version=2,
        )


def test_g2_keep_last_good_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Asserts existing cache is intact after any failure."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    cache_file = tmp_path / "IFSC.csv"
    original_data = (
        "BANK,IFSC,BRANCH,CENTRE,DISTRICT,STATE,ADDRESS,CONTACT,UPI,RTGS,CITY,NEFT,IMPS,MICR\n"
        "GoodBank,IFSC001,Main,Centre,Dist,State,Addr,123,true,true,City,true,true,123\n"
    )
    cache_file.write_text(original_data, encoding="utf-8")

    # Attempt failed refresh with corrupted data
    try:
        refresh_dataset("ifsc", mock_payload=b"corrupted garbage")
    except CdnRefreshError:
        pass

    assert cache_file.exists()
    assert cache_file.read_text(encoding="utf-8") == original_data


def test_g2_tmp_file_and_atomic_replace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Simulate crash between tmp write and replace; assert cache file is untouched."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    cache_file = tmp_path / "IFSC.csv"
    original_data = (
        "BANK,IFSC,BRANCH,CENTRE,DISTRICT,STATE,ADDRESS,CONTACT,UPI,RTGS,CITY,NEFT,IMPS,MICR\n"
        "Original,IFSC001,Main,Centre,Dist,State,Addr,123,true,true,City,true,true,123\n"
    )
    cache_file.write_text(original_data, encoding="utf-8")

    # Simulate crash right before atomic replace
    valid_payload = (
        b"BANK,IFSC,BRANCH,CENTRE,DISTRICT,STATE,ADDRESS,CONTACT,UPI,RTGS,CITY,NEFT,IMPS,MICR\n"
        b"NewBank,IFSC002,Main,Centre,Dist,State,Addr,123,true,true,City,true,true,123\n"
    )
    with pytest.raises(CdnRefreshError):
        refresh_dataset("ifsc", mock_payload=valid_payload, mock_crash_before_replace=True)

    assert cache_file.read_text(encoding="utf-8") == original_data
    # Ensure no lingering .tmp files
    tmp_files = list(tmp_path.glob("*.tmp*"))
    assert len(tmp_files) == 0


def test_g2_concurrent_refresh_locking(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Two concurrent refreshes use file locking and avoid race conditions."""
    monkeypatch.delenv("MCP_INDIA_STACK_NO_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(tmp_path))
    # Test that running refresh with lock already held yields safe handling
    success = refresh_dataset("ifsc", simulate_lock_contention=True)
    assert success is False
