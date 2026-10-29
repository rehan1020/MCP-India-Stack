"""Refresh and validate bundled datasets for mcp-india-stack.

Usage:
  python scripts/update_datasets.py --refresh-ifsc --refresh-pincode --refresh-hsn

HSN flow supports semi-manual staging:
  Place HSN_SAC.xlsx in staging/ then run --refresh-hsn.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import httpx
import openpyxl

from mcp_india_stack.utils.datasets import DATASET_CONFIG

__all__ = ["DATASET_CONFIG"]

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "mcp_india_stack" / "data"
STAGING = ROOT / "staging"

IFSC_URL = "https://github.com/razorpay/ifsc/releases/latest/download/IFSC.csv"
PINCODE_ZIP_URL = "https://download.geonames.org/export/zip/IN.zip"
HSN_HINT_URL = "https://tutorial.gst.gov.in/downloads/HSN_SAC.xlsx"

IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
VALID_RATES = {0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 12.0, 18.0, 28.0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as response:
        response.raise_for_status()
        with destination.open("wb") as out:
            for chunk in response.iter_bytes(1024 * 1024):
                out.write(chunk)


def refresh_ifsc() -> dict[str, Any]:
    target = DATA / "ifsc" / "IFSC.csv"
    _download(IFSC_URL, target)

    total = 0
    dupes = 0
    invalid = 0
    seen: set[str] = set()
    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            code = str(row.get("IFSC", "")).strip().upper()
            if not IFSC_PATTERN.match(code):
                invalid += 1
            if code in seen:
                dupes += 1
            seen.add(code)
    return {
        "file": str(target.relative_to(ROOT)).replace("\\", "/"),
        "rows": total,
        "invalid_ifsc_rows": invalid,
        "duplicate_ifsc_rows": dupes,
        "sha256": sha256(target),
        "source": IFSC_URL,
    }


def refresh_pincode() -> dict[str, Any]:
    zip_path = STAGING / "IN.zip"
    _download(PINCODE_ZIP_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.namelist()
        if "IN.txt" not in members:
            raise RuntimeError("IN.zip did not contain IN.txt")
        extracted = STAGING / "IN.txt"
        archive.extract("IN.txt", STAGING)

    out_path = DATA / "pincode" / "pincode.csv.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Pincode",
        "OfficeName",
        "OfficeType",
        "Delivery",
        "District",
        "StateName",
        "Circle",
        "Latitude",
        "Longitude",
    ]

    total = 0
    seen: set[tuple[str, str]] = set()
    invalid_pins = 0
    with extracted.open("r", encoding="utf-8", errors="replace") as src:
        with gzip.open(out_path, "wt", encoding="utf-8", newline="") as dst:
            writer = csv.writer(dst)
            writer.writerow(headers)

            for line in src:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 12:
                    continue
                pin = parts[1].strip()
                office = parts[2].strip()
                state = parts[3].strip()
                district = parts[5].strip()
                lat = parts[9].strip()
                lon = parts[10].strip()

                if not (pin.isdigit() and len(pin) == 6):
                    invalid_pins += 1
                    continue

                dedupe_key = (pin, office.lower())
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                writer.writerow(
                    [
                        pin,
                        office,
                        "SO",
                        "Delivery",
                        district,
                        state,
                        state,
                        lat,
                        lon,
                    ]
                )
                total += 1

    return {
        "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "rows": total,
        "invalid_pincode_rows": invalid_pins,
        "sha256": sha256(out_path),
        "source": PINCODE_ZIP_URL,
    }


def _extract_hsn_from_workbook(path: Path) -> list[dict[str, Any]]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header_idx = None
    for idx, row in enumerate(rows):
        normalized = [str(col).strip().lower() for col in row if col is not None]
        if any("hsn" in col for col in normalized) and any("desc" in col for col in normalized):
            header_idx = idx
            break

    if header_idx is None:
        raise ValueError("Could not find header row in HSN sheet")

    header = [str(c).strip().lower() if c is not None else "" for c in rows[header_idx]]
    hsn_idx = next(i for i, c in enumerate(header) if "hsn" in c or "code" in c)
    desc_idx = next(i for i, c in enumerate(header) if "desc" in c)
    rate_idx = next(
        (i for i, c in enumerate(header) if "rate" in c or "igst" in c or "gst" in c), None
    )

    extracted: list[dict[str, Any]] = []
    for row in rows[header_idx + 1 :]:
        if not any(row):
            continue
        hsn_raw = str(row[hsn_idx]).strip() if row[hsn_idx] is not None else ""
        digits = "".join(ch for ch in hsn_raw if ch.isdigit())
        if len(digits) not in {2, 4, 6, 8}:
            continue
        desc = str(row[desc_idx]).strip() if row[desc_idx] is not None else ""
        if not desc:
            continue

        rate = 18.0
        if rate_idx is not None and row[rate_idx] is not None:
            raw_rate = str(row[rate_idx]).replace("%", "").strip()
            try:
                parsed_rate = float(raw_rate)
                if parsed_rate in VALID_RATES:
                    rate = parsed_rate
            except ValueError:
                pass

        extracted.append({"hsn_code": digits, "description": desc, "gst_rate": rate})
    return extracted


def refresh_hsn() -> dict[str, Any]:
    staging_file = STAGING / "HSN_SAC.xlsx"
    if not staging_file.exists():
        try:
            _download(HSN_HINT_URL, staging_file)
        except Exception:
            pass

    if not staging_file.exists():
        return {
            "skipped": True,
            "reason": (
                "HSN requires manual download from GST portal. Place file at "
                f"{staging_file.relative_to(ROOT)}"
            ),
        }

    records = _extract_hsn_from_workbook(staging_file)
    if not records:
        raise RuntimeError("No HSN records extracted from staging workbook")

    out_csv = DATA / "hsn" / "hsn_master.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["hsn_code", "description", "gst_rate"])
        writer.writeheader()
        writer.writerows(records)

    return {
        "file": str(out_csv.relative_to(ROOT)).replace("\\", "/"),
        "rows": len(records),
        "sha256": sha256(out_csv),
        "source": str(staging_file.relative_to(ROOT)).replace("\\", "/"),
    }


def write_report(results: dict[str, Any]) -> None:
    report_path = ROOT / "data" / "validation_report.md"
    lines = ["# Data Validation Report", "", "Generated by scripts/update_datasets.py", ""]
    for name, payload in results.items():
        lines.append(f"## {name}")
        for key, val in payload.items():
            lines.append(f"- {key}: {val}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_checksums() -> None:
    import gzip
    import sys

    checksum_path = DATA / "dataset_checksums.json"
    checksum_payload = {}
    missing = []

    for name, config in DATASET_CONFIG.items():
        rel_path = config["bundled_path"].removeprefix("data/")
        abs_path = DATA / rel_path
        if not abs_path.exists():
            missing.append(name)
            continue

        # Count rows (informational only)
        rows = 0
        try:
            if abs_path.name.endswith(".gz"):
                with gzip.open(abs_path, "rt", encoding="utf-8") as f:
                    rows = sum(1 for _ in f)
            else:
                with open(abs_path, encoding="utf-8") as f:
                    rows = sum(1 for _ in f)
        except Exception:
            rows = 0

        checksum_payload[name] = {
            "file": f"src/mcp_india_stack/data/{rel_path}",
            "sha256": sha256(abs_path),
            "rows": rows,
        }

    has_all_manifest_entries = len(checksum_payload) == len(DATASET_CONFIG) and all(
        name in checksum_payload for name in DATASET_CONFIG
    )
    if missing or not has_all_manifest_entries:
        print(f"ERROR: Missing files or manifest entries: {missing}", file=sys.stderr)
        sys.exit(1)

    checksum_path.write_text(json.dumps(checksum_payload, indent=2), encoding="utf-8")
    print(
        f"Wrote checksums for {len(checksum_payload)} datasets to {checksum_path.relative_to(ROOT)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh datasets")
    parser.add_argument("--refresh-ifsc", action="store_true")
    parser.add_argument("--refresh-pincode", action="store_true")
    parser.add_argument("--refresh-hsn", action="store_true")
    parser.add_argument(
        "--write-checksums",
        action="store_true",
        help="Regenerate checksums without downloading",
    )
    args = parser.parse_args()

    STAGING.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    if args.refresh_ifsc:
        results["IFSC"] = refresh_ifsc()
    if args.refresh_pincode:
        results["PINCODE"] = refresh_pincode()
    if args.refresh_hsn:
        results["HSN"] = refresh_hsn()

    if results:
        write_report(results)
    write_checksums()
    if results:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
