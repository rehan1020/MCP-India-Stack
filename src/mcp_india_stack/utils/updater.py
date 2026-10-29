"""Dataset path resolution for bundled offline datasets."""

from __future__ import annotations

import logging
from pathlib import Path

from mcp_india_stack.utils.datasets import DATASET_CONFIG

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "data"


def _bundled_path(dataset_name: str) -> Path:
    """Return the path to the bundled dataset shipped with the package."""
    config = DATASET_CONFIG[dataset_name]
    return DATA_ROOT / config["bundled_path"].removeprefix("data/")


def get_dataset_path(dataset_name: str) -> Path:
    """Return the bundled path for a dataset.

    Args:
        dataset_name: Key from DATASET_CONFIG (e.g. "ifsc", "pincode", "hsn").

    Returns:
        Path to the bundled dataset file to load.
    """
    if dataset_name not in DATASET_CONFIG:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    return _bundled_path(dataset_name)
