"""Validate .pip-audit-ignore.toml and print --ignore-vuln CLI arguments."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


def validate_and_format_ignores(config_path: Path) -> list[str]:
    """Validate allowlist entries and return --ignore-vuln arguments."""
    if not config_path.exists():
        return []

    content = config_path.read_text(encoding="utf-8")
    if not content.strip():
        return []

    try:
        data = tomllib.loads(content)
    except Exception as exc:
        sys.stderr.write(f"Invalid TOML in {config_path}: {exc}\n")
        sys.exit(1)

    entries = data.get("ignore", [])
    if not isinstance(entries, list):
        sys.stderr.write(f"'ignore' must be a list of tables in {config_path}\n")
        sys.exit(1)

    today = date.today()
    args: list[str] = []
    required_fields = {"id", "package", "justification", "review_by"}

    for idx, entry in enumerate(entries):
        missing = required_fields - set(entry.keys())
        if missing:
            sys.stderr.write(
                f"Entry {idx} in {config_path} missing required fields: {sorted(missing)}\n"
            )
            sys.exit(1)

        advisory_id = str(entry["id"]).strip()
        package = str(entry["package"]).strip()
        justification = str(entry["justification"]).strip()
        review_by_str = str(entry["review_by"]).strip()

        if not advisory_id or not package or not justification:
            sys.stderr.write(
                f"Entry {idx} in {config_path} has empty id, package, or justification\n"
            )
            sys.exit(1)

        try:
            review_by = date.fromisoformat(review_by_str)
        except ValueError:
            sys.stderr.write(
                f"Entry {idx} in {config_path} has invalid review_by date: {review_by_str!r}\n"
            )
            sys.exit(1)

        if review_by < today:
            sys.stderr.write(
                f"Entry {idx} ({advisory_id}) in {config_path} "
                f"expired on {review_by} (review required)\n"
            )
            sys.exit(1)

        args.extend(["--ignore-vuln", advisory_id])

    return args


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate audit allowlist and print CLI args")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".pip-audit-ignore.toml"),
        help="Path to .pip-audit-ignore.toml (default: .pip-audit-ignore.toml)",
    )
    args = parser.parse_args()

    cli_args = validate_and_format_ignores(args.config)
    if cli_args:
        print(" ".join(cli_args))


if __name__ == "__main__":
    main()
