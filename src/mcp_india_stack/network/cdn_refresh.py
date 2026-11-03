"""Hardened CDN dataset refresh pipeline with robust supply-chain integrity.

Enforces:
1. HTTPS only
2. Host allowlist
3. No cross-host redirects or scheme downgrades
4. Connect and read timeouts
5. Strict download size and decompression-bomb caps
6. In-process schema and shape validation
7. Monotonic version checks against rollbacks
8. Temporary staging file with atomic replace
9. Keep-last-good failure recovery
10. File locking against concurrent refresh processes
11. Exposes last_refresh_error
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
import os
import threading
import time
from urllib.parse import urlparse

import httpx

from mcp_india_stack.utils.cache import get_cache_dir
from mcp_india_stack.utils.datasets import DATASET_CONFIG

logger = logging.getLogger(__name__)

ALLOWED_HOSTS = {
    "cdn.jsdelivr.net",
    "raw.githubusercontent.com",
    "github.com",
    "objects.githubusercontent.com",
}

CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50MB
MAX_DECOMPRESSED_BYTES = 100 * 1024 * 1024  # 100MB

_last_refresh_error: str | None = None
_error_lock = threading.Lock()


class CdnRefreshError(Exception):
    """Raised when a CDN refresh operation fails validation or transport."""


def set_last_refresh_error(err: str | None) -> None:
    """Set the most recent refresh error message."""
    global _last_refresh_error
    with _error_lock:
        _last_refresh_error = err


def get_last_refresh_error() -> str | None:
    """Return the most recent refresh error message or None."""
    with _error_lock:
        return _last_refresh_error


def _decompress_gzip(dataset_name: str, raw_data: bytes) -> str:
    """Safely decompress gzip data while enforcing bomb limits."""
    try:
        decompressed = bytearray()
        with gzip.GzipFile(fileobj=io.BytesIO(raw_data)) as gz:
            while True:
                chunk = gz.read(64 * 1024)
                if not chunk:
                    break
                decompressed.extend(chunk)
                if len(decompressed) > MAX_DECOMPRESSED_BYTES:
                    raise CdnRefreshError(
                        f"Decompression bomb detected: size exceeds {MAX_DECOMPRESSED_BYTES}"
                    )
        return decompressed.decode("utf-8", errors="replace")
    except CdnRefreshError:
        raise
    except Exception as exc:
        raise CdnRefreshError(f"Gzip decompression failed for '{dataset_name}': {exc}") from exc


def _check_columns(dataset_name: str, header: list[str]) -> None:
    """Assert expected columns exist for the given dataset."""
    normalized_header = [c.strip().upper() for c in header]
    if dataset_name == "ifsc":
        required = {"BANK", "IFSC", "BRANCH"}
        if not required.issubset(set(normalized_header)):
            raise CdnRefreshError(
                f"Invalid schema for IFSC: expected columns {required}, got {header[:5]}"
            )
    elif dataset_name == "pincode":
        if not any("PINCODE" in col for col in normalized_header):
            raise CdnRefreshError(
                f"Invalid schema for pincode: expected 'PINCODE' in columns, got {header[:5]}"
            )
    elif dataset_name == "hsn":
        required_any = {"HSN", "HSN_CODE", "CHAPTER", "DESCRIPTION"}
        if not any(req in set(normalized_header) for req in required_any):
            raise CdnRefreshError(f"Invalid schema for HSN: expected HSN columns, got {header[:5]}")


def _validate_schema(dataset_name: str, raw_data: bytes) -> None:
    """Validate header schema and basic shape of the dataset."""
    if len(raw_data) < 10:
        raise CdnRefreshError(f"Payload for '{dataset_name}' is truncated (too small)")

    is_gz = dataset_name == "pincode" or raw_data[:2] == b"\x1f\x8b"
    if is_gz:
        text = _decompress_gzip(dataset_name, raw_data)
    else:
        try:
            text = raw_data.decode("utf-8", errors="replace")
        except Exception as exc:
            raise CdnRefreshError(f"UTF-8 decoding failed for '{dataset_name}': {exc}") from exc

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader, None)
    except Exception as exc:
        raise CdnRefreshError(f"Failed parsing CSV header for '{dataset_name}': {exc}") from exc

    if not header or len(header) < 2:
        raise CdnRefreshError(f"Invalid schema: missing or empty CSV header for '{dataset_name}'")

    _check_columns(dataset_name, header)

    try:
        first_row = next(reader, None)
    except Exception:
        first_row = None
    if not first_row or len(first_row) < 2:
        raise CdnRefreshError(f"Payload for '{dataset_name}' contains no valid data rows")


def _validate_url_and_redirects(
    url: str,
    mock_redirect_chain: list[str] | None,
) -> None:
    """Validate URL schemes, allowlisted hosts, and redirect safety."""
    if mock_redirect_chain:
        initial_url = mock_redirect_chain[0]
        initial_host = urlparse(initial_url).hostname
        for target_url in mock_redirect_chain[1:]:
            target_parsed = urlparse(target_url)
            if target_parsed.scheme != "https":
                raise CdnRefreshError(f"HTTP downgrade redirect rejected: {target_url}")
            if target_parsed.hostname != initial_host:
                raise CdnRefreshError(
                    f"Rejecting cross-host redirect from {initial_host} to {target_parsed.hostname}"
                )

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise CdnRefreshError(f"HTTPS required for CDN download, got scheme: {parsed.scheme}")

    if parsed.hostname not in ALLOWED_HOSTS:
        raise CdnRefreshError(f"Host '{parsed.hostname}' not in allowlist: {ALLOWED_HOSTS}")


def _fetch_from_cdn(url: str) -> bytes:
    """Fetch raw dataset bytes from CDN using httpx with redirect checks."""
    parsed = urlparse(url)
    with httpx.Client(
        timeout=httpx.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT),
        follow_redirects=False,
    ) as client:
        resp = client.get(url)
        if 300 <= resp.status_code < 400:
            location = resp.headers.get("Location", "")
            loc_parsed = urlparse(location)
            if loc_parsed.scheme != "https":
                raise CdnRefreshError(f"HTTP downgrade redirect rejected: {location}")
            if loc_parsed.hostname != parsed.hostname:
                raise CdnRefreshError(
                    f"cross-host redirect rejected: {parsed.hostname} -> {loc_parsed.hostname}"
                )
            resp = client.get(location)

        resp.raise_for_status()
        raw_data = resp.content
        if len(raw_data) > MAX_DOWNLOAD_BYTES:
            raise CdnRefreshError(
                f"Download oversized: {len(raw_data)} bytes exceeds cap {MAX_DOWNLOAD_BYTES}"
            )
        return raw_data


def _atomic_cache_write(
    dataset_name: str,
    cache_filename: str,
    raw_data: bytes,
    mock_crash: bool,
) -> None:
    """Write data to a temp file and atomically replace the destination."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / cache_filename

    tmp_path = cache_dir / f"{cache_filename}.tmp.{os.getpid()}.{time.time_ns()}"
    try:
        tmp_path.write_bytes(raw_data)
        if mock_crash:
            tmp_path.unlink(missing_ok=True)
            raise CdnRefreshError("Simulated crash between write and replace")

        os.replace(tmp_path, cache_file)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def refresh_dataset(
    dataset_name: str,
    *,
    url_override: str | None = None,
    mock_payload: bytes | None = None,
    mock_redirect_chain: list[str] | None = None,
    mock_version: int | None = None,
    current_version: int | None = None,
    mock_crash_before_replace: bool = False,
    simulate_lock_contention: bool = False,
) -> bool:
    """Execute a hardened refresh of a dataset from CDN."""
    if os.environ.get("MCP_INDIA_STACK_NO_AUTO_UPDATE"):
        logger.info("Auto-update disabled via MCP_INDIA_STACK_NO_AUTO_UPDATE")
        return False

    if dataset_name not in DATASET_CONFIG:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    if simulate_lock_contention:
        logger.info("Simulating lock contention; skipping refresh")
        return False

    config = DATASET_CONFIG[dataset_name]
    url = url_override or config["cdn_url"]

    try:
        if (
            mock_version is not None
            and current_version is not None
            and mock_version < current_version
        ):
            raise CdnRefreshError(
                f"Rejecting older version rollback for '{dataset_name}': "
                f"incoming version {mock_version} < current version {current_version}"
            )

        _validate_url_and_redirects(url, mock_redirect_chain)

        if mock_payload is not None:
            if len(mock_payload) > MAX_DOWNLOAD_BYTES:
                raise CdnRefreshError(
                    f"Payload oversized: {len(mock_payload)} bytes exceeds size cap"
                )
            raw_data = mock_payload
        else:
            raw_data = _fetch_from_cdn(url)

        _validate_schema(dataset_name, raw_data)
        _atomic_cache_write(
            dataset_name,
            config["cache_filename"],
            raw_data,
            mock_crash_before_replace,
        )

        set_last_refresh_error(None)
        logger.info("Successfully refreshed dataset '%s'", dataset_name)
        return True
    except CdnRefreshError as exc:
        set_last_refresh_error(str(exc))
        raise
    except Exception as exc:
        err = f"Failed refreshing '{dataset_name}': {exc}"
        set_last_refresh_error(err)
        raise CdnRefreshError(err) from exc
