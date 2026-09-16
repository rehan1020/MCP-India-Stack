"""Database connection module for MCP India Stack.

Provides optional live database connectivity as an alternative to bundled data.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def is_db_connected() -> bool:
    """Check if database is connected."""
    return False
