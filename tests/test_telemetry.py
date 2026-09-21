import json

from mcp_india_stack import telemetry


def test_telemetry_pepper_hmac(monkeypatch, tmp_path):
    log_path = tmp_path / "telemetry.jsonl"
    monkeypatch.setenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", "test-secret-pepper")
    monkeypatch.setenv("MCP_INDIA_STACK_LOG_PATH", str(log_path))

    # Reload telemetry module to pick up env vars
    import importlib

    importlib.reload(telemetry)

    assert telemetry._ENABLED is True

    digest = telemetry._hash_input("my-secret-id")
    assert len(digest) == 16

    # Prove it's salted and differs from raw SHA256
    import hashlib

    raw_sha = hashlib.sha256(b"my-secret-id").hexdigest()[:16]
    assert digest != raw_sha

    # Test logging
    telemetry.log_tool_usage("test_tool", "my-secret-id", 42.0, "success")

    with open(log_path) as f:
        line = f.read()
    data = json.loads(line)

    assert data["tool_name"] == "test_tool"
    assert data["hashed_input"] == digest
    assert data["latency_ms"] == 42.0
    assert data["result_type"] == "success"


def test_telemetry_disabled_without_pepper(monkeypatch, tmp_path):
    monkeypatch.delenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", raising=False)
    log_path = tmp_path / "telemetry.jsonl"
    monkeypatch.setenv("MCP_INDIA_STACK_LOG_PATH", str(log_path))

    import importlib

    importlib.reload(telemetry)

    assert telemetry._ENABLED is False

    # Should not write
    telemetry.log_tool_usage("test_tool", "my-secret-id", 42.0, "success")
    assert not log_path.exists()


def test_telemetry_rotation(monkeypatch, tmp_path):
    log_path = tmp_path / "telemetry_rot.jsonl"
    monkeypatch.setenv("MCP_INDIA_STACK_TELEMETRY_PEPPER", "secret")
    monkeypatch.setenv("MCP_INDIA_STACK_LOG_PATH", str(log_path))

    import importlib

    from mcp_india_stack import telemetry

    importlib.reload(telemetry)

    # Force a very small maxBytes for testing rotation
    for handler in telemetry._telemetry_logger.handlers:
        if hasattr(handler, "maxBytes"):
            handler.maxBytes = 50  # 50 bytes

    for i in range(10):
        telemetry.log_tool_usage("tool", str(i), 1.0, "success")

    # Check that rotation happened (there should be backup files like telemetry_rot.jsonl.1)
    files = list(tmp_path.glob("telemetry_rot.jsonl*"))
    assert len(files) > 1
