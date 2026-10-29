"""Tests for bundled dataset path resolution and removal of runtime refresh."""

from __future__ import annotations

import ast
import hashlib
import importlib.resources
import importlib.util
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from mcp_india_stack.utils.updater import get_dataset_path


def test_ta1_all_datasets_in_manifest_and_sha256_matches() -> None:
    """TA1: Every dataset in scripts/update_datasets.py DATASET_CONFIG has matching SHA-256."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "update_datasets.py"
    spec = importlib.util.spec_from_file_location("update_datasets_script", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    dataset_config = mod.DATASET_CONFIG
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "mcp_india_stack"
        / "data"
        / "dataset_checksums.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for name in dataset_config:
        assert name in manifest, f"Dataset {name} missing from manifest"
        entry = manifest[name]
        file_path = Path(__file__).resolve().parents[1] / entry["file"]
        assert file_path.exists(), f"File {file_path} does not exist"
        actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_sha == entry["sha256"], (
            f"SHA mismatch for {name}: expected {entry['sha256']}, got {actual_sha}"
        )


def test_ta2_no_network_client_imports_in_utils() -> None:
    """TA2: AST check: no import of network clients in src/mcp_india_stack/utils/*.py."""
    forbidden = {"httpx", "requests", "urllib", "http", "socket", "aiohttp"}
    utils_dir = Path(__file__).resolve().parents[1] / "src" / "mcp_india_stack" / "utils"
    for py_file in utils_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    assert root_mod not in forbidden, (
                        f"Forbidden import '{alias.name}' in {py_file.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    assert root_mod not in forbidden, (
                        f"Forbidden from-import '{node.module}' in {py_file.name}"
                    )


def test_ta3_loader_ignores_planted_garbage_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """TA3: Planted garbage in MCP_INDIA_STACK_CACHE_DIR is ignored; bundled data loaded."""
    import importlib

    import mcp_india_stack.utils.loader as loader

    # Ensure real function is loaded even if autouse fixture patched it
    importlib.reload(loader)
    try:
        assert hasattr(loader.load_ifsc_index, "cache_clear")
        loader.load_ifsc_index.cache_clear()
        baseline_index = loader.load_ifsc_index()
        baseline_count = len(baseline_index)

        planted_cache = tmp_path / "planted_cache"
        planted_cache.mkdir(parents=True, exist_ok=True)
        planted_file = planted_cache / "IFSC.csv"
        planted_file.write_text("corrupted,garbage,data\n1,2,3\n", encoding="utf-8")
        planted_gz = planted_cache / "ifsc.csv.gz"
        planted_gz.write_bytes(b"corrupted gz bytes")

        monkeypatch.setenv("MCP_INDIA_STACK_CACHE_DIR", str(planted_cache))

        loader.load_ifsc_index.cache_clear()
        test_index = loader.load_ifsc_index()
        assert len(test_index) == baseline_count
        loader.load_ifsc_index.cache_clear()
    finally:
        loader.load_ifsc_index.cache_clear()


def test_ta4_cli_refresh_all_prints_removal_and_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """TA4: --refresh-all prints removal notice, exits 2, and does no network/socket connections."""
    import socket
    import sys

    from mcp_india_stack.server import main

    def no_connect(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Network socket connection attempted during --refresh-all")

    monkeypatch.setattr(socket.socket, "connect", no_connect)
    monkeypatch.setattr(sys, "argv", ["mcp-india-stack", "--refresh-all"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "dataset refresh was removed; upgrade the package to receive new data" in captured.err


def test_ta5_packaged_manifest_and_datasets_exist() -> None:
    """TA5: Packaged manifest and datasets exist via importlib.resources and in built wheel."""
    ref = importlib.resources.files("mcp_india_stack")
    data_dir = ref / "data"
    assert (data_dir / "dataset_checksums.json").is_file()
    assert (data_dir / "ifsc" / "IFSC.csv").is_file()
    assert (data_dir / "pincode" / "pincode.csv.gz").is_file()
    assert (data_dir / "hsn" / "hsn_master.csv").is_file()

    dist_dir = Path(__file__).resolve().parents[1] / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    if wheels:
        latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)
        with zipfile.ZipFile(latest_wheel) as zf:
            namelist = zf.namelist()
            assert "mcp_india_stack/data/dataset_checksums.json" in namelist
            assert "mcp_india_stack/data/ifsc/IFSC.csv" in namelist
            assert "mcp_india_stack/data/pincode/pincode.csv.gz" in namelist
            assert "mcp_india_stack/data/hsn/hsn_master.csv" in namelist


def test_get_dataset_path_valid() -> None:
    """get_dataset_path returns bundled path for known datasets."""
    path = get_dataset_path("ifsc")
    assert path.exists()
    assert path.name == "IFSC.csv"


def test_get_dataset_path_unknown_raises() -> None:
    """get_dataset_path raises ValueError for unknown dataset."""
    with pytest.raises(ValueError, match="Unknown dataset"):
        get_dataset_path("nonexistent_dataset_name")
