import pytest

import mcp_india_stack.database as db_module
from mcp_india_stack.database import init_db_connection, is_db_connected, query_db


def test_database_health_check_failed(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://fake-db")

    # Mock httpx client to return 500
    class MockClient:
        def get(self, url, **kwargs):
            class MockResponse:
                status_code = 500

            return MockResponse()

    monkeypatch.setattr("httpx.Client", lambda timeout: MockClient())

    assert init_db_connection() is False
    assert is_db_connected() is False


def test_database_query_non_200(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://fake-db")

    # Force connection to not be None
    class MockConnection:
        def get(self, url, params=None):
            class MockResponse:
                status_code = 500

            return MockResponse()

    db_module._db_connection = MockConnection()

    result = query_db("SELECT * FROM users")
    assert result == []

    db_module._db_connection = None


def test_database_query_not_read_only(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://fake-db")
    db_module._db_connection = "dummy"
    db_module._DB_READ_ONLY = True

    with pytest.raises(ValueError, match="Only read-only queries allowed"):
        query_db("UPDATE users SET name='test'")

    db_module._DB_READ_ONLY = False

    db_module._db_connection = None


def test_database_query_exception(monkeypatch):
    monkeypatch.setenv("MCP_INDIA_STACK_DB_URL", "http://fake-db")

    class MockConnection:
        def get(self, url, params=None):
            raise ConnectionError("Timeout")

    db_module._db_connection = MockConnection()
    result = query_db("SELECT * FROM users")
    assert result == []
    db_module._db_connection = None
