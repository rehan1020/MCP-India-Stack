"""Dataset CDN configuration for auto-update mechanism.

NOTE: The IFSC URL is pinned to a specific Razorpay IFSC release tag.
When a new Razorpay IFSC release ships, update the tag in the URL below.
Check releases at: https://github.com/razorpay/ifsc/releases
"""

from __future__ import annotations

from typing import TypedDict


class DatasetConfig(TypedDict):
    """Configuration for a single dataset."""

    cdn_url: str
    cache_filename: str
    stale_after_days: int
    bundled_path: str


DATASET_CONFIG: dict[str, DatasetConfig] = {
    "ifsc": {
        "cdn_url": (
            "https://github.com/razorpay/ifsc/releases/download/"
            "v2.0.57/IFSC.csv"
        ),
        "cache_filename": "IFSC.csv",
        "stale_after_days": 30,
        "bundled_path": "data/ifsc/IFSC.csv",
    },
    "pincode": {
        "cdn_url": (
            "https://cdn.jsdelivr.net/gh/rehan1020/MCP-India-Stack"
            "@main/src/mcp_india_stack/data/pincode/pincode.csv.gz"
        ),
        "cache_filename": "pincode.csv.gz",
        "stale_after_days": 90,
        "bundled_path": "data/pincode/pincode.csv.gz",
    },
    "hsn": {
        "cdn_url": (
            "https://cdn.jsdelivr.net/gh/rehan1020/MCP-India-Stack"
            "@main/src/mcp_india_stack/data/hsn/hsn_master.csv"
        ),
        "cache_filename": "hsn_master.csv",
        "stale_after_days": 180,
        "bundled_path": "data/hsn/hsn_master.csv",
    },
}
