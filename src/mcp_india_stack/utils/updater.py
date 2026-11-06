"""Dataset path resolution for bundled offline datasets."""

from __future__ import annotations

import logging
from pathlib import Path

from mcp_india_stack.authenticity.manifest import get_cached_manifest, verify_dataset_file
from mcp_india_stack.utils.cache import get_cache_dir
from mcp_india_stack.utils.datasets import DATASET_CONFIG

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "data"


def _bundled_path(dataset_name: str) -> Path:
    """Return the path to the bundled dataset shipped with the package."""
    config = DATASET_CONFIG[dataset_name]
    return DATA_ROOT / config["bundled_path"].removeprefix("data/")


def get_dataset_path(dataset_name: str) -> Path:
    """Return the active path for a dataset (verified cache if present, else bundled).

    Args:
        dataset_name: Key from DATASET_CONFIG (e.g. "ifsc", "pincode", "hsn").

    Returns:
        Path to the dataset file to load.
    """
    if dataset_name not in DATASET_CONFIG:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    config = DATASET_CONFIG[dataset_name]
    cache_file = get_cache_dir() / config["cache_filename"]
    cached_m = get_cached_manifest(dataset_name)

    if cache_file.exists() and cached_m is not None:
        ok, msg = verify_dataset_file(dataset_name, cache_file, cached_m)
        if ok:
            return cache_file
        logger.warning(
            "Cached dataset '%s' failed signature/checksum verification (%s); using bundled copy",
            dataset_name,
            msg,
        )

    return _bundled_path(dataset_name)
