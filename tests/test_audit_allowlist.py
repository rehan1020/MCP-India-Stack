"""Unit tests for scripts/audit_allowlist.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit_allowlist import validate_and_format_ignores


def test_empty_config(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.toml"
    empty_file.write_text("", encoding="utf-8")
    args = validate_and_format_ignores(empty_file)
    assert args == []


def test_valid_config(tmp_path: Path) -> None:
    cfg = tmp_path / "valid.toml"
    cfg.write_text(
        """
[[ignore]]
id = "CVE-2026-0001"
package = "test-pkg"
justification = "Testing"
review_by = "2099-01-01"
""",
        encoding="utf-8",
    )
    args = validate_and_format_ignores(cfg)
    assert args == ["--ignore-vuln", "CVE-2026-0001"]


def test_missing_field_exits(tmp_path: Path) -> None:
    cfg = tmp_path / "missing.toml"
    cfg.write_text(
        """
[[ignore]]
id = "CVE-2026-0001"
package = "test-pkg"
# missing justification and review_by
""",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        validate_and_format_ignores(cfg)
    assert exc.value.code != 0


def test_expired_review_by_exits(tmp_path: Path) -> None:
    cfg = tmp_path / "expired.toml"
    cfg.write_text(
        """
[[ignore]]
id = "CVE-2026-0001"
package = "test-pkg"
justification = "Testing"
review_by = "2020-01-01"
""",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc:
        validate_and_format_ignores(cfg)
    assert exc.value.code != 0
