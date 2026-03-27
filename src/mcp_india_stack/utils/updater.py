"""Background dataset updater with CDN fetch and integrity checks.

Rules:
1. Never block tool execution — stale data triggers background thread.
2. Opt-out via MCP_INDIA_STACK_NO_AUTO_UPDATE environment variable.
3. Graceful fallback — CDN failures are logged silently, never crash.
4. CDN fetch timeout is 10 seconds.
5. Staleness is based on cached file modification timestamp.
6. Downloaded files are integrity-checked before replacing cache.
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from mcp_india_stack.utils.cache import get_cache_dir
from mcp_india_stack.utils.datasets import DATASET_CONFIG

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "data"

_CDN_TIMEOUT = 10  # seconds
_update_locks: dict[str, threading.Lock] = {}


def _get_lock(dataset_name: str) -> threading.Lock:
    """Return a per-dataset lock, creating it if needed."""
    if dataset_name not in _update_locks:
        _update_locks[dataset_name] = threading.Lock()
    return _update_locks[dataset_name]


def _bundled_path(dataset_name: str) -> Path:
    """Return the path to the bundled dataset shipped with the package."""
    config = DATASET_CONFIG[dataset_name]
    return DATA_ROOT / config["bundled_path"].removeprefix("data/")


def _cached_path(dataset_name: str) -> Path:
    """Return the expected cache file path."""
    config = DATASET_CONFIG[dataset_name]
    return get_cache_dir() / config["cache_filename"]


def _is_stale(path: Path, stale_after_days: int) -> bool:
    """Check if a cached file is older than the staleness threshold."""
    if not path.exists():
        return True
    mtime = path.stat().st_mtime
    age_days = (time.time() - mtime) / 86400
    return age_days > stale_after_days


def _auto_update_disabled() -> bool:
    """Check if auto-update is disabled via environment variable."""
    return os.environ.get("MCP_INDIA_STACK_NO_AUTO_UPDATE") is not None


def _validate_csv(data: bytes) -> bool:
    """Check that data is a valid CSV with at least a header row."""
    try:
        text = data.decode("utf-8")
        reader = csv.reader(io.StringIO(text))
        header = next(reader, None)
        return header is not None and len(header) > 0
    except Exception:
        return False


def _validate_gzip(data: bytes) -> bool:
    """Check that data is a valid gzip archive containing CSV."""
    try:
        with gzip.open(io.BytesIO(data), "rt", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            return header is not None and len(header) > 0
    except Exception:
        return False


def _fetch_and_cache(dataset_name: str) -> bool:
    """Fetch dataset from CDN and write to cache. Returns True on success."""
    config = DATASET_CONFIG[dataset_name]
    url = config["cdn_url"]
    cache_file = _cached_path(dataset_name)

    try:
        with httpx.Client(timeout=_CDN_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.content
    except Exception as exc:
        logger.warning("CDN fetch failed for %s: %s", dataset_name, exc)
        return False

    # Integrity check
    is_gz = config["cache_filename"].endswith(".gz")
    if is_gz:
        valid = _validate_gzip(data)
    else:
        valid = _validate_csv(data)

    if not valid:
        logger.warning("Integrity check failed for %s — discarding download", dataset_name)
        return False

    # Atomic-ish write: write to temp then rename
    tmp_path = cache_file.with_suffix(cache_file.suffix + ".tmp")
    try:
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(data)
        tmp_path.replace(cache_file)
    except Exception as exc:
        logger.warning("Failed writing cache for %s: %s", dataset_name, exc)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False

    logger.info("Updated cached dataset: %s", dataset_name)
    return True


def get_dataset_path(dataset_name: str) -> Path:
    """Return the best available path for a dataset.

    Priority:
    1. Valid cached file (exists and not stale) — use directly.
    2. Stale cached file — use it, trigger background update for next request.
    3. No cached file — use bundled, trigger background update.

    Args:
        dataset_name: Key from DATASET_CONFIG (e.g. "ifsc", "pincode", "hsn").

    Returns:
        Path to the dataset file to load.
    """
    if dataset_name not in DATASET_CONFIG:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    config = DATASET_CONFIG[dataset_name]
    cache = _cached_path(dataset_name)
    bundled = _bundled_path(dataset_name)

    if cache.exists():
        if _is_stale(cache, config["stale_after_days"]) and not _auto_update_disabled():
            trigger_background_update(dataset_name)
        return cache

    # No cache — use bundled and trigger background update
    if not _auto_update_disabled():
        trigger_background_update(dataset_name)
    return bundled


def trigger_background_update(dataset_name: str) -> None:
    """Spawn a daemon thread to fetch and cache the latest dataset.

    Non-blocking: returns immediately regardless of download outcome.
    Thread-safe: only one update per dataset at a time.
    """
    if _auto_update_disabled():
        return

    lock = _get_lock(dataset_name)
    if not lock.acquire(blocking=False):
        # Another update is already running for this dataset
        return

    def _update() -> None:
        try:
            _fetch_and_cache(dataset_name)
        finally:
            lock.release()

    thread = threading.Thread(target=_update, daemon=True, name=f"update-{dataset_name}")
    thread.start()


def force_refresh_all() -> dict[str, bool]:
    """Synchronously refresh all datasets from CDN.

    Returns:
        Dict mapping dataset name to success boolean.
    """
    results: dict[str, bool] = {}
    for name in DATASET_CONFIG:
        results[name] = _fetch_and_cache(name)
    return results


def get_cache_info(dataset_name: str) -> dict[str, Any]:
    """Return cache metadata for a dataset (used for warnings in tool responses)."""
    cache = _cached_path(dataset_name)
    if cache.exists():
        mtime = cache.stat().st_mtime
        last_updated = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        return {"cached": True, "last_updated": last_updated, "path": str(cache)}
    return {"cached": False, "last_updated": None, "path": str(_bundled_path(dataset_name))}
