"""Test G5: Root hygiene and moved files integrity."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_g5_root_files_moved_to_docs() -> None:
    """Assert release_notes_v0.6.5.md and tiers.txt are moved out of root into docs/."""
    # Must NOT exist in root
    assert not (ROOT / "release_notes_v0.6.5.md").exists(), (
        "release_notes_v0.6.5.md still in repo root"
    )
    assert not (ROOT / "tiers.txt").exists(), "tiers.txt still in repo root"

    # Must exist in docs/
    assert (ROOT / "docs" / "release_notes_v0.6.5.md").exists(), (
        "release_notes_v0.6.5.md missing from docs/"
    )
    assert (ROOT / "docs" / "tiers.txt").exists(), "tiers.txt missing from docs/"


def test_g5_no_dangling_references_to_old_root_paths() -> None:
    """Assert no source or markdown files contain dangling references to root paths."""
    for py_or_md_file in ROOT.rglob("*"):
        if py_or_md_file.suffix not in (".py", ".md", ".txt", ".yml", ".yaml"):
            continue
        if py_or_md_file.name == "test_g05_root_hygiene.py":
            continue
        parts = py_or_md_file.parts
        ignored_dirs = (".venv", "venv", ".git", "site-packages", "dist", "build")
        if any(ignored in parts for ignored in ignored_dirs):
            continue

        try:
            content = py_or_md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        assert "release_notes_v0.6.5.md" not in content or "docs/release_notes_v0.6.5.md" in content

        for line in content.splitlines():
            if (
                "tiers.txt" in line
                and "docs/tiers.txt" not in line
                and py_or_md_file.name != "tiers.txt"
            ):
                raise AssertionError(
                    f"Dangling reference to root tiers.txt in {py_or_md_file.relative_to(ROOT)}: "
                    f"{line}"
                )
