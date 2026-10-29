"""Verify git tag matches package version in pyproject.toml."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


def get_pyproject_version(pyproject_path: Path) -> str:
    """Extract version from pyproject.toml."""
    content = pyproject_path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(content)
        return str(data["project"]["version"])
    except Exception as err:
        # Fallback regex
        m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            return m.group(1)
        raise ValueError("Could not parse version from pyproject.toml") from err


def main() -> None:
    parser = argparse.ArgumentParser(description="Check git tag matches pyproject version")
    parser.add_argument("--tag", type=str, default=None, help="Git tag (e.g. v0.6.9)")
    args = parser.parse_args()

    tag = args.tag or os.environ.get("GITHUB_REF_NAME")
    if not tag and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        tag = sys.argv[1]

    if not tag:
        sys.stderr.write("No tag specified (via --tag, argument, or GITHUB_REF_NAME)\n")
        sys.exit(1)

    clean_tag = tag.lstrip("v")
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"

    try:
        version = get_pyproject_version(pyproject)
    except Exception as exc:
        sys.stderr.write(f"Error reading pyproject version: {exc}\n")
        sys.exit(1)

    if clean_tag != version:
        sys.stderr.write(
            f"Tag version mismatch! Git tag: {tag!r} (normalized: {clean_tag!r}) "
            f"!= pyproject version: {version!r}\n"
        )
        sys.exit(1)

    print(f"Tag version matches pyproject.toml: {version}")


if __name__ == "__main__":
    main()
