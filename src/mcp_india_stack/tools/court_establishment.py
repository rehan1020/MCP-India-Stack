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
    return json.loads(  # type: ignore[return-value]
        path.read_text(encoding="utf-8")
    )


def lookup_court_establishment_code(code: str) -> dict[str, Any]:
    """
    Lookup a court establishment using its code.

    Input:
    - code (str): 2-letter state prefix (e.g. MH) or
      4-character establishment code (e.g. MHPU).

    Output: For exact match — court_name, district, state,
    court_type. For prefix match — list of matching courts.

    Example prompt: "Lookup court establishment code MHPU"

    Limitations: Data is community-curated and may not be
    exhaustive.
    """
    errors: list[str] = []
    warnings: list[str] = []

    clean_code = str(code).strip().upper()
    data_dict = _load_court_establishments()

    if not data_dict:
        warnings.append("Court establishments database not found or empty.")

    # Try exact 4-character match first
    result = data_dict.get(clean_code)

    if result:
        return _flatten(
            build_response(
                success=True,
                data={
                    "code": clean_code,
                    "court_name": result.get("court_name", ""),
                    "district": result.get("district", ""),
                    "state": result.get("state", ""),
                    "state_code": result.get("state_code", ""),
                    "court_type": result.get("court_type", ""),
                },
                errors=errors,
                warnings=warnings,
            )
        )

    # Try prefix match (e.g. "MH" → all MH* courts)
    if len(clean_code) <= 3:
        prefix_matches = []
        for k, v in data_dict.items():
            if k.startswith(clean_code):
                prefix_matches.append(
                    {
                        "code": k,
                        "court_name": v.get("court_name", ""),
                        "district": v.get("district", ""),
                        "state": v.get("state", ""),
                        "court_type": v.get("court_type", ""),
                    }
                )

        if prefix_matches:
            return _flatten(
                build_response(
                    success=True,
                    data={
                        "query": clean_code,
                        "match_type": "prefix",
                        "count": len(prefix_matches),
                        "courts": prefix_matches,
                    },
                    errors=errors,
                    warnings=warnings,
                )
            )

    errors.append(f"Court establishment code '{clean_code}' not found.")
    return _flatten(
        build_response(
            success=False,
            data={"code": clean_code},
            errors=errors,
            warnings=warnings,
        )
    )
