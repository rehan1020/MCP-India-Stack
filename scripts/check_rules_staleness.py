#!/usr/bin/env python3
"""CLI utility to audit statutory rules staleness and verification age.

Implements G6(e):
- Checks if active rule set is past effective_to
- Checks if last_verified is older than 180 days
- Returns exit code 1 if stale rules detected, 0 otherwise
- Supports frozen date via --as-of for deterministic CI tests
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from mcp_india_stack.tools.rules_metadata import check_rules_staleness


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit rule sets for staleness and expiry.")
    parser.add_argument(
        "--as-of",
        dest="as_of",
        type=str,
        default=None,
        help="Audit date in YYYY-MM-DD format (defaults to current date).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output issues as JSON.",
    )
    args = parser.parse_args()

    as_of_date = date.fromisoformat(args.as_of) if args.as_of else None
    issues = check_rules_staleness(as_of_date)

    if args.json:
        print(json.dumps(issues, indent=2))
        return 1 if issues else 0

    if not issues:
        audit_date_str = as_of_date.isoformat() if as_of_date else date.today().isoformat()
        print(f"All statutory rule sets are fresh and verified as of {audit_date_str}.")
        return 0

    print(f"STALENESS WARNING: Found {len(issues)} rule set issue(s):")
    for idx, issue in enumerate(issues, 1):
        print(f"[{idx}] {issue['table_id']} ({issue['name']}): {issue['message']}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
