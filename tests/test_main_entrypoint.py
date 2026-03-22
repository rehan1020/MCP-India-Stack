import runpy


def test_module_entrypoint_calls_server_main(monkeypatch) -> None:
    calls: list[str] = []

    def fake_main() -> None:
        calls.append("called")

    monkeypatch.setattr("mcp_india_stack.server.main", fake_main)
    runpy.run_module("mcp_india_stack", run_name="__main__")

    assert calls == ["called"]
