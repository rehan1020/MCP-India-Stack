"""Permission tier classification for MCP India Stack tools.

This enum defines escalating permission levels for tools, enabling future
access control and audit logging as write/submit tools are added.

The calculate → submit danger boundary is critical:
- READ_ONLY and LOOKUP_LIVE tools can be retried freely
- INITIATE tools begin transactions but are reversible (e.g., draft submission)
- SUBMIT tools commit irreversible changes (e.g., tax filing, payment initiation)
"""

from enum import IntEnum


class PermissionTier(IntEnum):
    """
    Ascending permission levels for tool access control.

    Tier | Description
    ---- | -----------
    0    | READ_ONLY — No external call. Regex/checksum only.
    1    | LOOKUP_LIVE — Read-only external API call.
    2    | INITIATE — Begins a transaction. Reversible.
    3    | SUBMIT — Commits. Irreversible.
    """

    READ_ONLY = 0
    LOOKUP_LIVE = 1
    INITIATE = 2
    SUBMIT = 3
