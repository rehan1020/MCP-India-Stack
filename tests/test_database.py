from mcp_india_stack import database


def test_database_dead_code_removed():
    assert not hasattr(database, "query_db")
    assert not hasattr(database, "init_db_connection")
    assert not hasattr(database, "get_db_config")
    assert not hasattr(database, "close_db_connection")
    assert not hasattr(database, "_DB_URL")


def test_is_db_connected_stub():
    assert database.is_db_connected() is False
