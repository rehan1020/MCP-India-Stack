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
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _score_match(query: str, item: dict[str, Any]) -> float:
    """Score how well a query matches an article.

    Higher score = better match. Uses keyword matching
    first (weighted higher), then falls back to
    suit_type substring matching.
    """
    q = query.lower().strip()
    score = 0.0

    # Check keywords (weighted heavily)
    keywords = item.get("keywords", [])
    for kw in keywords:
        kw_lower = kw.lower()
        if q == kw_lower:
            score += 10.0  # Exact keyword match
        elif q in kw_lower or kw_lower in q:
            score += 5.0  # Partial keyword match

    # Check suit_type substring (lower weight)
    suit_type = item.get("suit_type", "").lower()
    if q in suit_type:
        score += 2.0
    elif suit_type in q:
        score += 1.0

    # Penalise very long suit_type descriptions
    # (prefer more specific matches)
    if score > 0 and len(suit_type) > 100:
        score -= 0.5

    return score


def calculate_limitation_deadline(suit_type: str, cause_of_action_date: str) -> dict[str, Any]:
    """
    Calculate the limitation period deadline under the
    Limitation Act, 1963.

    Input:
    - suit_type (str): Type of suit or application to
      search for.
    - cause_of_action_date (str): Date the cause of action
      arose (YYYY-MM-DD).

    Output: suit_type, matches (list of matched articles
    with deadlines sorted by relevance), errors, warnings

    Example prompt: "Calculate limitation for money
    recovery from 2023-01-01"

    Limitations: Does not account for court holidays,
    exclusions, or valid delays.
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

    scored: list[tuple[float, dict[str, Any]]] = []
    for item in data:
        s = _score_match(suit_type, item)
        if s > 0:
            scored.append((s, item))

    # Sort by score descending (best match first)
    scored.sort(key=lambda x: x[0], reverse=True)

    for _score, item in scored:
        item_suit_type = item.get("suit_type", "")
        years = float(item.get("limitation_years", 0))

        # Handle years > 365 as days (e.g. 90 days)
        if years <= 365:
            try:
                deadline = start_date.replace(year=start_date.year + int(years))
            except ValueError:
                # Handle Feb 29 edge case
                deadline = start_date.replace(
                    year=start_date.year + int(years),
                    day=28,
                )

            if years % 1 != 0:
                extra = int((years % 1) * 365.25)
                deadline += datetime.timedelta(days=extra)
        else:
            deadline = start_date + datetime.timedelta(days=int(years))

        is_barred = deadline < today
        days_rem = (deadline - today).days

        matches.append(
            {
                "matched_article": item.get("article", ""),
                "suit_type": item_suit_type,
                "limitation_years": years,
                "cause_of_action_date": (cause_of_action_date),
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
