"""Check requirements.txt lockfile for drift against pyproject.toml."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def clean_lines(text: str) -> list[str]:
    """Return non-empty, non-comment lines sorted for comparison."""
    return sorted(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def check_lock(pyproject_path: Path, lock_path: Path) -> int:
    """Regenerate lock in temp file and compare non-comment lines."""
    if not lock_path.exists():
        sys.stderr.write(f"Lockfile {lock_path} does not exist\n")
        return 1

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "uv",
            "pip",
            "compile",
            str(pyproject_path),
            str(lock_path),
            "--extra",
            "dev",
            "--python-version",
            "3.10",
            "--universal",
            "-o",
            str(tmp_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.stderr.write(f"uv pip compile failed: {res.stderr}\n")
            return 1

        existing = clean_lines(lock_path.read_text(encoding="utf-8"))
        generated = clean_lines(tmp_path.read_text(encoding="utf-8"))

        diff_added = set(generated) - set(existing)
        diff_removed = set(existing) - set(generated)

        if diff_added or diff_removed:
            sys.stderr.write("Lockfile drift detected!\n")
            if diff_added:
                sys.stderr.write(f"Added in regenerated lock: {sorted(diff_added)}\n")
            if diff_removed:
                sys.stderr.write(f"Missing in regenerated lock: {sorted(diff_removed)}\n")
            return 1

        print("Lockfile matches pyproject.toml dependencies (no drift).")
        return 0
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Check requirements.txt lockfile for drift.")
    parser.add_argument("--pyproject", type=Path, default=None, help="Path to pyproject.toml")
    parser.add_argument("--lockfile", type=Path, default=None, help="Path to requirements.txt")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    pyproject = args.pyproject or root / "pyproject.toml"
    lock = args.lockfile or root / "requirements.txt"
    sys.exit(check_lock(pyproject, lock))


if __name__ == "__main__":
    main()
