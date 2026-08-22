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
def _load_bare_acts() -> list[dict[str, Any]]:
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "legal" / "bare_acts.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


@functools.lru_cache(maxsize=1)
def _load_crosswalk() -> list[dict[str, Any]]:
    path = (
        pathlib.Path(__file__).resolve().parent.parent / "data" / "legal" / "ipc_bns_crosswalk.json"
    )
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore


def _lookup_section(act: str, section: str) -> dict[str, Any]:
    acts = _load_bare_acts()
    for item in acts:
        if item.get("act") == act and str(item.get("section")) == str(section):
            return item
    return {}


def lookup_ipc_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Indian Penal Code (IPC).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, punishment, cognizable, bailable,
    bns_crosswalk, success, errors

    Example prompt: "Look up IPC section 420"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("IPC", section)
    errors = []
    if not data:
        errors.append(f"IPC section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="IPC")
    if cw.get("success"):
        data["bns_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def lookup_bns_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Bharatiya Nyaya Sanhita (BNS).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, punishment, cognizable, bailable,
    ipc_crosswalk, success, errors

    Example prompt: "Look up BNS section 316"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("BNS", section)
    errors = []
    if not data:
        errors.append(f"BNS section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="BNS")
    if cw.get("success"):
        data["ipc_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def lookup_crpc_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Code of Criminal Procedure (CrPC).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, bnss_crosswalk, success, errors

    Example prompt: "Look up CrPC section 154"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("CrPC", section)
    errors = []
    if not data:
        errors.append(f"CrPC section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="CrPC")
    if cw.get("success"):
        data["bnss_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def lookup_bnss_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Bharatiya Nagarik Suraksha Sanhita (BNSS).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, crpc_crosswalk, success, errors

    Example prompt: "Look up BNSS section 173"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("BNSS", section)
    errors = []
    if not data:
        errors.append(f"BNSS section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="BNSS")
    if cw.get("success"):
        data["crpc_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def lookup_evidence_act_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Indian Evidence Act (IEA).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, bsa_crosswalk, success, errors

    Example prompt: "Look up IEA section 65B"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("IEA", section)
    errors = []
    if not data:
        errors.append(f"IEA section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="IEA")
    if cw.get("success"):
        data["bsa_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def lookup_bsa_section(section: str) -> dict[str, Any]:
    """
    Lookup a section in the Bharatiya Sakshya Adhiniyam (BSA).

    Input:
    - section (str): Section number to look up.

    Output: act, section, title, summary, iea_crosswalk, success, errors

    Example prompt: "Look up BSA section 63"

    Limitations: Offline data, community-curated, may not reflect latest amendments.
    """
    data = _lookup_section("BSA", section)
    errors = []
    if not data:
        errors.append(f"BSA section {section} not found.")

    cw = decode_ipc_bns_crosswalk(section, from_act="BSA")
    if cw.get("success"):
        data["iea_crosswalk"] = cw.get("target_section")

    return _flatten(
        build_response(
            success=len(errors) == 0,
            data={"source": "offline_static", **data} if data else {"source": "offline_static"},
            errors=errors,
            warnings=["Data is community-curated"],
        )
    )


def decode_ipc_bns_crosswalk(section: str, from_act: str = "IPC") -> dict[str, Any]:
    """
    Look up equivalent sections between old and new criminal laws.

    Input:
    - section (str): Section number.
    - from_act (str): Source act ("IPC", "BNS", "CrPC", "BNSS", "IEA", "BSA").

    Output: original_act, original_section, target_act, target_section, success, errors

    Example prompt: "What is the BNS equivalent of IPC 420?"

    Limitations: Offline data, community-curated.
    """
    crosswalk = _load_crosswalk()
    errors = []

    mapping = {
        "IPC": ("ipc_section", "bns_section", "BNS"),
        "BNS": ("bns_section", "ipc_section", "IPC"),
        "CrPC": ("crpc_section", "bnss_section", "BNSS"),
        "BNSS": ("bnss_section", "crpc_section", "CrPC"),
        "IEA": ("iea_section", "bsa_section", "BSA"),
        "BSA": ("bsa_section", "iea_section", "IEA"),
    }

    if from_act not in mapping:
        errors.append(f"Invalid from_act: {from_act}")
        return _flatten(build_response(success=False, data={}, errors=errors))

    source_key, target_key, target_act = mapping[from_act]

    for item in crosswalk:
        if str(item.get(source_key)) == str(section):
            return _flatten(
                build_response(
                    success=True,
                    data={
                        "original_act": from_act,
                        "original_section": section,
                        "target_act": target_act,
                        "target_section": item.get(target_key),
                        "source": "offline_static",
                    },
                    errors=[],
                )
            )

    errors.append(f"Crosswalk not found for {from_act} section {section}")
    return _flatten(build_response(success=False, data={}, errors=errors))
