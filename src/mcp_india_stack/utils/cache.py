"""Cache directory management using platformdirs."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_cache_dir


def get_cache_dir() -> Path:
    """Return the platform-specific cache directory for mcp-india-stack.

    Paths produced:
        Windows: C:\\Users\\{user}\\AppData\\Local\\rehan1020\\mcp-india-stack\\Cache
        macOS:   ~/Library/Caches/mcp-india-stack
        Linux:   ~/.cache/mcp-india-stack
    """
    import os

    env_cache = os.environ.get("MCP_INDIA_STACK_CACHE_DIR")
    if env_cache:
        cache = Path(env_cache)
    else:
        cache = Path(user_cache_dir("mcp-india-stack", "rehan1020"))
    cache.mkdir(parents=True, exist_ok=True)
    return cache
