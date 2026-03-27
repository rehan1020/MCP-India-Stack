"""Lazy data loading and in-memory indexes for static datasets."""

from __future__ import annotations

import csv
import gzip
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import polars as pl

from mcp_india_stack.utils.updater import get_dataset_path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "data"


class DataLoadError(RuntimeError):
    """Raised when a packaged dataset cannot be loaded."""


def _normalize_hsn_code(value: object) -> str:
    """Normalize HSN/SAC code by keeping digits only."""
    return re.sub(r"\D", "", str(value)).strip()


def _must_exist(path: Path, label: str) -> Path:
    if not path.exists():
        raise DataLoadError(
            f"{label} dataset not found at '{path}'. "
            "Reinstall with 'pip install --force-reinstall mcp-india-stack'."
        )
    return path


@lru_cache(maxsize=1)
def load_state_codes() -> dict[str, dict[str, str]]:
    """Load state code mapping keyed by two-digit GST code."""
    path = _must_exist(DATA_ROOT / "state_codes" / "state_codes.json", "State code")
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:  # pragma: no cover
        raise DataLoadError(f"Failed loading state code dataset: {exc}") from exc
    return cast(dict[str, dict[str, str]], payload["codes"])


@lru_cache(maxsize=1)
def load_upi_handles() -> dict[str, dict[str, str]]:
    """Load curated UPI handle/provider mapping."""
    path = _must_exist(DATA_ROOT / "upi" / "upi_handles.json", "UPI handle")
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:  # pragma: no cover
        raise DataLoadError(f"Failed loading UPI handle dataset: {exc}") from exc
    return cast(dict[str, dict[str, str]], payload["handles"])


@lru_cache(maxsize=1)
def load_ifsc_index() -> dict[str, dict[str, Any]]:
    """Load IFSC CSV once and build O(1) code lookup."""
    path = _must_exist(get_dataset_path("ifsc"), "IFSC")
    try:
        df = pl.read_csv(
            path,
            infer_schema_length=5000,
            schema_overrides={
                "BANK": pl.Utf8,
                "IFSC": pl.Utf8,
                "BRANCH": pl.Utf8,
                "ADDRESS": pl.Utf8,
                "CONTACT": pl.Utf8,
                "CITY": pl.Utf8,
                "DISTRICT": pl.Utf8,
                "STATE": pl.Utf8,
                "CENTRE": pl.Utf8,
                "MICR": pl.Utf8,
                "UPI": pl.Utf8,
                "RTGS": pl.Utf8,
                "NEFT": pl.Utf8,
                "IMPS": pl.Utf8,
                "SWIFT": pl.Utf8,
            },
        )
    except Exception as exc:  # pragma: no cover
        raise DataLoadError(f"Failed loading IFSC dataset: {exc}") from exc

    required_cols = {
        "BANK",
        "IFSC",
        "BRANCH",
        "ADDRESS",
        "CONTACT",
        "CITY",
        "DISTRICT",
        "STATE",
        "MICR",
        "UPI",
        "RTGS",
        "NEFT",
        "IMPS",
        "SWIFT",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise DataLoadError(f"IFSC dataset missing required columns: {sorted(missing)}")

    rows = df.to_dicts()
    return {str(row["IFSC"]).upper(): row for row in rows}


@lru_cache(maxsize=1)
def load_pincode_index() -> dict[str, list[dict[str, str]]]:
    """Load gzipped pincode CSV and build one-to-many pincode index."""
    path = _must_exist(get_dataset_path("pincode"), "Pincode")
    index: dict[str, list[dict[str, str]]] = {}
    try:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                pin = str(row.get("Pincode", "")).strip()
                if not pin:
                    continue
                index.setdefault(pin, []).append(row)
    except Exception as exc:  # pragma: no cover
        raise DataLoadError(f"Failed loading pincode dataset: {exc}") from exc
    return index


@lru_cache(maxsize=1)
def load_hsn_index() -> dict[str, list[dict[str, Any]]]:
    """Load HSN/SAC master and index by code."""
    path = _must_exist(get_dataset_path("hsn"), "HSN/SAC")
    try:
        df = pl.read_csv(
            path,
            infer_schema_length=2000,
            schema_overrides={
                "HSNCode": pl.Utf8,
                "Description": pl.Utf8,
            },
        )
    except Exception as exc:  # pragma: no cover
        raise DataLoadError(f"Failed loading HSN dataset: {exc}") from exc

    required_cols = {
        "HSNCode",
        "Description",
        "CGST_Rate",
        "SGST_Rate",
        "IGST_Rate",
        "CESS_Rate",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise DataLoadError(f"HSN dataset missing required columns: {sorted(missing)}")

    rows = df.to_dicts()
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        code = _normalize_hsn_code(row.get("HSNCode", ""))
        if not code:
            continue
        normalized_row = dict(row)
        normalized_row["HSNCode"] = code
        out.setdefault(code, []).append(normalized_row)
    return out


@lru_cache(maxsize=1)
def load_hsn_rows() -> list[dict[str, Any]]:
    """Load full HSN/SAC row list for keyword search."""
    index = load_hsn_index()
    rows: list[dict[str, Any]] = []
    for code_rows in index.values():
        rows.extend(code_rows)
    return rows
