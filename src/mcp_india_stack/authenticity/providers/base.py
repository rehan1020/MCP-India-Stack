"""Abstract base class contract for all registry verification providers."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from mcp_india_stack.authenticity.providers.models import ProviderResult


class BaseRegistryProvider(ABC):
    """Abstract interface defining the contract for registry verification backends.

    Providers query authoritative or opt-in registry endpoints to promote
    entities to Level A4 (Live Registry Attestation).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g., 'gstn_portal', 'mca_v3', 'fixture_provider')."""

    @property
    @abstractmethod
    def supported_entities(self) -> list[str]:
        """List of canonical entity types supported by this provider (e.g. ['gstin', 'pan'])."""

    @abstractmethod
    async def verify(self, entity_type: str, identifier: str, **kwargs: Any) -> ProviderResult:
        """Asynchronously verify an identifier against the registry backend."""

    def verify_sync(self, entity_type: str, identifier: str, **kwargs: Any) -> ProviderResult:
        """Synchronous wrapper for verification."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in event loop (e.g., inside an async MCP handler)
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.verify(entity_type, identifier, **kwargs))
                return future.result()
        return asyncio.run(self.verify(entity_type, identifier, **kwargs))
