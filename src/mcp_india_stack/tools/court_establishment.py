from __future__ import annotations

import functools
import json
import pathlib
from typing import Any

from mcp_india_stack.utils.responses import build_response


def _flatten(r: dict[str, Any]) -> dict[str, Any]:
    """Hoist data keys to top-level for backwards compatibility."""
    if "data" in r and isinstance(r["data"], dict):
        r.update(r["data"])
    return r


@functools.lru_cache(maxsize=1)
def _load_court_establishments() -> dict[str, dict[str, Any]]:
    path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "data"
        / "legal"
        / "court_establishments.json"
    )
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def lookup_court_establishment_code(code: str) -> dict[str, Any]:
    """
    Lookup a court establishment using its 4-character code.

    Input:
    - code (str): The 4-character court establishment code (e.g., from a CNR number).

    Output: court_name, district, state_code, court_type, success, errors, warnings

    Example prompt: "Lookup court establishment code DLCT"

    Limitations: Data is community-curated and may not be exhaustive.
    """
    errors: list[str] = []
    warnings: list[str] = []

    clean_code = str(code).strip().upper()
    data_dict = _load_court_establishments()

    if not data_dict:
        warnings.append("Court establishments database not found or empty.")

    result = data_dict.get(clean_code)

    if not result:
        errors.append(f"Court establishment code '{clean_code}' not found.")
        return _flatten(
            build_response(
                success=False, data={"code": clean_code}, errors=errors, warnings=warnings
            )
        )

    return _flatten(
        build_response(
            success=True,
            data={
                "code": clean_code,
                "court_name": result.get("court_name", ""),
                "district": result.get("district", ""),
                "state_code": result.get("state_code", ""),
                "court_type": result.get("court_type", ""),
            },
            errors=errors,
            warnings=warnings,
        )
    )
