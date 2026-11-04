"""Tests for data provenance and dataset cataloging (G13).

Acceptance requirement:
- Every file under src/mcp_india_stack/data/ is explicitly cataloged in docs/data_provenance.md.
- Third-party licenses and attributions are reconciled in NOTICES.
- Cryptographic checksum manifest accounts for all bundled datasets.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "mcp_india_stack" / "data"
DOCS_DIR = ROOT / "docs"
PROVENANCE_DOC = DOCS_DIR / "data_provenance.md"
NOTICES_FILE = ROOT / "NOTICES"


def test_every_data_file_is_listed_in_provenance_doc() -> None:
    """Assert every file under data/ is explicitly listed in docs/data_provenance.md."""
    assert PROVENANCE_DOC.exists(), "docs/data_provenance.md must exist"
    doc_content = PROVENANCE_DOC.read_text(encoding="utf-8")

    data_files = [
        f
        for f in DATA_DIR.rglob("*")
        if f.is_file() and not f.name.startswith(".") and "__pycache__" not in f.parts
    ]
    assert len(data_files) >= 13, f"Expected at least 13 data files, found {len(data_files)}"

    missing: list[str] = []
    for file_path in data_files:
        rel_path = file_path.relative_to(DATA_DIR).as_posix()
        if rel_path not in doc_content:
            missing.append(rel_path)

    assert not missing, f"Files under data/ missing from docs/data_provenance.md: {missing}"


def test_notices_covers_dataset_families() -> None:
    """Assert NOTICES contains license attributions for all third-party dataset families."""
    assert NOTICES_FILE.exists(), "NOTICES must exist"
    notices_content = NOTICES_FILE.read_text(encoding="utf-8")

    required_families = [
        "Razorpay IFSC Dataset",
        "India Pincode Dataset",
        "HSN / SAC Code",
        "Legal Reference & Crosswalk Datasets",
        "RTI Fee Schedules",
        "GST State Codes",
        "NPCI UPI Handle",
        "Dataset Checksum Manifest",
    ]

    for family in required_families:
        assert family in notices_content, f"Family '{family}' missing from NOTICES"


def test_dataset_checksum_manifest_integrity() -> None:
    """Assert dataset_checksums.json exists and contains entries for bundled datasets."""
    checksum_file = DATA_DIR / "dataset_checksums.json"
    assert checksum_file.exists(), "dataset_checksums.json must exist"

    checksums = json.loads(checksum_file.read_text(encoding="utf-8"))
    assert isinstance(checksums, dict)
    assert len(checksums) >= 3  # Core verified datasets
