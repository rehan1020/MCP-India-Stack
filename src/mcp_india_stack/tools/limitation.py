from __future__ import annotations

import datetime
import functools
import json
import pathlib
from typing import Any


@functools.lru_cache(maxsize=1)
def _load_limitation_periods() -> list[dict[str, Any]]:
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "data"
        / "legal"
        / "limitation_periods.json"
    )
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def calculate_limitation_deadline(suit_type: str, cause_of_action_date: str) -> dict[str, Any]:
    """
    Calculate the limitation period deadline under the Limitation Act, 1963.

    Input:
    - suit_type (str): Type of suit or application to search for.
    - cause_of_action_date (str): Date the cause of action arose (YYYY-MM-DD).

    Output: suit_type, matches (list of matched articles with deadlines), errors, warnings

    Example prompt: "Calculate limitation for money recovery from 2023-01-01"

    Limitations: Does not account for court holidays, exclusions, or valid delays.
    """
    errors: list[str] = []
    warnings: list[str] = []
    matches: list[dict[str, Any]] = []

    try:
        start_date = datetime.date.fromisoformat(cause_of_action_date)
    except ValueError:
        errors.append("cause_of_action_date must be in YYYY-MM-DD format.")
        return {"errors": errors, "warnings": warnings}

    today = datetime.date.today()
    data = _load_limitation_periods()

    if not data:
        warnings.append("Limitation periods data file not found or empty.")

    query = suit_type.lower()

    for item in data:
        item_suit_type = item.get("suit_type", "")
        if query in item_suit_type.lower():
            years = float(item.get("limitation_years", 0))
            deadline = start_date.replace(year=start_date.year + int(years))

            # Simplified day addition if fractional years exist
            if years % 1 != 0:
                extra_days = int((years % 1) * 365.25)
                deadline += datetime.timedelta(days=extra_days)

            is_barred = deadline < today
            days_rem = (deadline - today).days

            matches.append(
                {
                    "matched_article": item.get("article_number", ""),
                    "suit_type": item_suit_type,
                    "limitation_years": years,
                    "cause_of_action_date": cause_of_action_date,
                    "deadline_date": deadline.isoformat(),
                    "starts_from": item.get("starts_from", ""),
                    "is_time_barred": is_barred,
                    "days_remaining": days_rem,
                }
            )

    if not matches:
        warnings.append(f"No matching suit type found for '{suit_type}'.")

    return {
        "suit_type": suit_type,
        "cause_of_action_date": cause_of_action_date,
        "matches": matches,
        "errors": errors,
        "warnings": warnings,
    }
