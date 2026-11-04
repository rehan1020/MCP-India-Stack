"""Check all relative markdown links in repository for dead references."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_links() -> int:
    broken: list[tuple[str, str, str]] = []
    total = 0

    for md_file in ROOT.rglob("*.md"):
        # Ignore virtual environments, git objects, or staging dirs
        parts = md_file.parts
        if any(
            ignored in parts
            for ignored in (".venv", "venv", ".git", "site-packages", "dist", "build")
        ):
            continue

        text = md_file.read_text(encoding="utf-8")
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
        for _title, link in links:
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            total += 1
            target_path_str = link.split("#")[0]
            if not target_path_str:
                continue
            target = (md_file.parent / target_path_str).resolve()
            if not target.exists():
                broken.append((str(md_file.relative_to(ROOT)), link, str(target)))

    print(f"Checked {total} relative markdown links.")
    if broken:
        print(f"FAILED: Found {len(broken)} broken relative link(s):")
        for file_rel, link, target in broken:
            print(f"  {file_rel}: '{link}' -> {target}")
        return 1

    print("SUCCESS: All relative links resolved successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(check_links())
