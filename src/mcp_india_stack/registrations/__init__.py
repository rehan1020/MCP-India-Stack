"""Tool registration modules organized by domain.

Importing this package triggers side-effect registration of all 78 tools
onto the shared FastMCP instance from mcp_india_stack.app.
"""

from mcp_india_stack.registrations import (  # noqa: F401
    banking,
    finance,
    kyc,
    legal,
    lookup,
    markets,
    tax,
)
