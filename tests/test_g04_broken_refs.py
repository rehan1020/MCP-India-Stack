"""Tests for G4: Legal notice completeness and relative link integrity."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_g4_legal_notice_exists_and_covers_required_clauses() -> None:
    """Assert LEGAL_NOTICE.md exists and covers all required disclosures."""
    legal_notice_file = ROOT / "LEGAL_NOTICE.md"
    assert legal_notice_file.exists(), "LEGAL_NOTICE.md is missing from repository root"

    content = legal_notice_file.read_text(encoding="utf-8").lower()

    # 1. No government affiliation
    assert "no government affiliation" in content or "not affiliated with" in content
    # 2. Not legal advice
    assert "not legal advice" in content
    # 3. Data accuracy and as_of
    assert "data accuracy" in content
    assert "as_of" in content or "last_verified" in content
    # 4. Personal data and DPDP
    assert "personal data" in content
    assert "dpdp" in content


def test_g4_no_broken_architecture_png_reference() -> None:
    """Assert assets/architecture.png is not referenced anywhere in markdown."""
    for md_file in ROOT.rglob("*.md"):
        if ".venv" in str(md_file) or ".git" in str(md_file):
            continue
        content = md_file.read_text(encoding="utf-8")
        assert "assets/architecture.png" not in content, (
            f"Found broken architecture.png reference in {md_file.name}"
        )


def test_g4_relative_link_checker() -> None:
    """Assert all relative markdown links point to existing files."""
    broken: list[tuple[str, str, str]] = []

    for md_file in ROOT.rglob("*.md"):
        if ".venv" in str(md_file) or ".git" in str(md_file):
            continue
        text = md_file.read_text(encoding="utf-8")
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for _title, link in links:
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path_str = link.split("#")[0]
            if not target_path_str:
                continue
            target = (md_file.parent / target_path_str).resolve()
            if not target.exists():
                broken.append((str(md_file.relative_to(ROOT)), link, str(target)))

    assert len(broken) == 0, f"Found broken relative links: {broken}"
