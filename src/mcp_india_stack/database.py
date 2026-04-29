"""Database connection module for MCP India Stack.

Provides optional live database connectivity as an alternative to bundled data.
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

_DB_URL = os.environ.get("MCP_INDIA_STACK_DB_URL")
_DB_READ_ONLY = os.environ.get("MCP_INDIA_STACK_DB_READONLY", "1") == "1"
_db_connection = None


def get_db_config() -> dict[str, Any]:
    """Get database configuration."""
    return {
        "db_url_set": _DB_URL is not None,
        "db_url": _DB_URL[:20] + "..." if _DB_URL else None,
        "read_only": _DB_READ_ONLY,
    }


def is_db_connected() -> bool:
    """Check if database is connected."""
    return _db_connection is not None


def init_db_connection() -> bool:
    """Initialize database connection with health check.

    Returns True if connected, False if not.
    """
    global _db_connection

    if not _DB_URL:
        _db_connection = None
        return False

    try:
        # Use httpx for database HTTP API (assuming REST-based DB)
        # For actual SQL databases, you'd use appropriate drivers
        client = httpx.Client(timeout=5.0)

        # Health check endpoint
        response = client.get(f"{_DB_URL.rstrip('/')}/health")

        if response.status_code == 200:
            _db_connection = client
            logger.info("Database connection established successfully")
            return True
        else:
            logger.warning(f"Database health check failed: {response.status_code}")
            _db_connection = None
            return False

    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Falling back to offline mode.")
        _db_connection = None
        return False


def query_db(query: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    """Execute a read-only query against the database.

    Args:
        query: SQL query or API endpoint
        params: Query parameters

    Returns:
        List of result rows as dictionaries
    """
    if not _db_connection:
        raise RuntimeError("Database not connected")

    if _DB_READ_ONLY:
        # Ensure query is read-only (basic check)
        query_upper = query.upper().strip()
        if any(
            keyword in query_upper
            for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
        ):
            raise ValueError("Only read-only queries allowed")

    try:
        base_url = _DB_URL.rstrip("/") if _DB_URL else ""
        response = _db_connection.get(f"{base_url}/query", params={"q": query, "params": params})
        if response.status_code == 200:
            return cast(list[dict[str, Any]], response.json())
        return []
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return []


def close_db_connection() -> None:
    """Close database connection."""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None
        logger.info("Database connection closed")
