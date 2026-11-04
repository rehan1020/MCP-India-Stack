"""Tests for G3: README drift verification against tool registry and pyproject version."""

from __future__ import annotations

import re
from pathlib import Path

from mcp_india_stack import __version__
from mcp_india_stack.app import TOOL_TIERS

ROOT = Path(__file__).resolve().parents[1]


def test_g3_readme_tool_count_matches_registry() -> None:
    """Assert README mentions exact registered tool count (78)."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    registered_count = len(TOOL_TIERS)
    assert registered_count == 78

    # Assert old 76 count is gone
    assert "76 dedicated tools" not in readme
    assert "76 offline-first tool modules" not in readme

    # Assert new 78 count is present
    assert f"{registered_count} dedicated tools" in readme or f"{registered_count} tools" in readme


def test_g3_readme_catalog_tool_parity() -> None:
    """Every registered tool is in the README catalog and vice versa."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    lines = readme.splitlines()
    in_catalog = False
    catalog_tools: set[str] = set()

    for line in lines:
        if "Tool Catalog" in line and line.startswith("##"):
            in_catalog = True
            continue
        if in_catalog and line.startswith("## "):
            in_catalog = False
            break
        if in_catalog and line.startswith("- "):
            m = re.search(r"`([a-z0-9_]+)`", line)
            if m:
                catalog_tools.add(m.group(1))

    registered_tools = set(TOOL_TIERS.keys())
    assert catalog_tools == registered_tools, (
        f"Mismatch between catalog and registry. Missing: {registered_tools - catalog_tools}, "
        f"Extra: {catalog_tools - registered_tools}"
    )


def test_g3_readme_version_matches_pyproject() -> None:
    """Assert README launch notes / metadata matches pyproject.toml version."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    m = re.search(r'version\s*=\s*"([^"]+)"', pyproject)
    assert m is not None
    pyproject_version = m.group(1)
    assert pyproject_version == __version__

    # README launch notes should reference current pyproject version
    assert f"`{pyproject_version}` package metadata" in readme


def test_g3_v04_history_moved_to_changelog() -> None:
    """Assert v0.4.x bug-fix history is in CHANGELOG and removed from README."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    # In changelog
    assert "## [0.4.1]" in changelog
    assert "Masked Aadhaar number leakage" in changelog

    # Removed from README
    assert "### Bug fixes in v0.4.1" not in readme
    assert "### Bug fixes in v0.4.2" not in readme
