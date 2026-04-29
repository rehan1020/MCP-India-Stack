#!/usr/bin/env python3
"""Enforce per-file coverage minimums."""

import json
import sys
from pathlib import Path

MINIMUMS = {
    "src/mcp_india_stack/__init__.py": 100,
    "src/mcp_india_stack/__main__.py": 100,
    "src/mcp_india_stack/database.py": 90,
    "src/mcp_india_stack/normalization.py": 90,
    "src/mcp_india_stack/permission_tiers.py": 100,
    "src/mcp_india_stack/server.py": 90,
    "src/mcp_india_stack/telemetry.py": 90,
    "src/mcp_india_stack/tools/__init__.py": 90,
    "src/mcp_india_stack/tools/aadhaar.py": 85,
    "src/mcp_india_stack/tools/advance_tax.py": 80,
    "src/mcp_india_stack/tools/bbps.py": 90,
    "src/mcp_india_stack/tools/capital_gains.py": 90,
    "src/mcp_india_stack/tools/cin.py": 90,
    "src/mcp_india_stack/tools/din.py": 80,
    "src/mcp_india_stack/tools/driving_license.py": 90,
    "src/mcp_india_stack/tools/fssai.py": 85,
    "src/mcp_india_stack/tools/gst_calculator.py": 85,
    "src/mcp_india_stack/tools/gstin.py": 90,
    "src/mcp_india_stack/tools/hra.py": 90,
    "src/mcp_india_stack/tools/hsn.py": 90,
    "src/mcp_india_stack/tools/ifsc.py": 95,
    "src/mcp_india_stack/tools/income_tax.py": 90,
    "src/mcp_india_stack/tools/pan.py": 90,
    "src/mcp_india_stack/tools/passport.py": 85,
    "src/mcp_india_stack/tools/pincode.py": 90,
    "src/mcp_india_stack/tools/state_code.py": 100,
    "src/mcp_india_stack/tools/surcharge.py": 90,
    "src/mcp_india_stack/tools/tds.py": 90,
    "src/mcp_india_stack/tools/upi.py": 85,
    "src/mcp_india_stack/tools/voter_id.py": 85,
    "src/mcp_india_stack/utils/__init__.py": 100,
    "src/mcp_india_stack/utils/cache.py": 90,
    "src/mcp_india_stack/utils/datasets.py": 90,
    "src/mcp_india_stack/utils/loader.py": 90,
    "src/mcp_india_stack/utils/responses.py": 95,
    "src/mcp_india_stack/utils/updater.py": 90,
}


def normalize_path(path: str) -> str:
    """Normalize path to match MINIMUMS keys."""
    return path.replace("\\", "/")


def main() -> int:
    coverage_path = Path("coverage.json")
    if not coverage_path.exists():
        print("ERROR: coverage.json not found. Run pytest --cov first.")
        return 1

    with open(coverage_path) as f:
        data = json.load(f)

    files = data.get("files", {})
    failures = []

    for path, minimum in MINIMUMS.items():
        normalized = normalize_path(path)
        found = False
        for file_key in files:
            if normalize_path(file_key) == normalized:
                found = True
                coverage = files[file_key]["summary"]["percent_covered"]
                if coverage < minimum:
                    failures.append(f"  {path}: {coverage:.1f}% < {minimum}%")
                break

        if not found:
            failures.append(f"  {path}: NOT FOUND IN COVERAGE")

    if failures:
        print("COVERAGE FAILURES:")
        for f in failures:
            print(f)
        print(f"\n{len(failures)} file(s) below minimum")
        return 1
    else:
        print("All files meet coverage minimums")
        return 0


if __name__ == "__main__":
    sys.exit(main())
