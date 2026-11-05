"""Reference implementation of a registry provider reading local JSON fixtures."""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any

from mcp_india_stack.authenticity.providers.base import BaseRegistryProvider
from mcp_india_stack.authenticity.providers.models import ProviderResult, ProviderStatus


class FixtureProvider(BaseRegistryProvider):
    """Reference implementation that reads recorded registry responses from a local directory.

    Zero network, zero external credentials. Ideal for testing, staging, and air-gapped demo
    environments.
    """

    def __init__(self, fixture_dir: Path | str | None = None) -> None:
        if fixture_dir:
            self._dir = Path(fixture_dir)
        elif os.environ.get("MCP_INDIA_STACK_FIXTURE_DIR"):
            self._dir = Path(os.environ["MCP_INDIA_STACK_FIXTURE_DIR"])
        else:
            self._dir = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "providers"

    @property
    def name(self) -> str:
        return "FixtureProvider"

    @property
    def supported_entities(self) -> list[str]:
        return ["gstin", "pan", "cin", "din", "aadhaar", "upi", "ifsc"]

    async def verify(self, entity_type: str, identifier: str, **kwargs: Any) -> ProviderResult:
        """Read pre-recorded JSON fixture matching identifier."""
        clean_id = identifier.strip().upper()
        clean_entity = entity_type.strip().lower()

        # Candidates: {dir}/{entity}/{id}.json or {dir}/{id}.json
        candidate1 = self._dir / clean_entity / f"{clean_id}.json"
        candidate2 = self._dir / f"{clean_id}.json"
        target_file = candidate1 if candidate1.exists() else candidate2

        if not target_file.exists():
            return ProviderResult(
                status=ProviderStatus.NOT_FOUND,
                details={},
                raw_evidence=None,
                source=self.name,
                as_of=datetime.date.today().isoformat(),
                error_message=f"No fixture found for entity '{clean_entity}' with id '{clean_id}'",
            )

        try:
            content = json.loads(target_file.read_text(encoding="utf-8"))
            raw_status = str(content.get("status", "ACTIVE")).upper()
            try:
                status = ProviderStatus(raw_status)
            except ValueError:
                status = ProviderStatus.ERROR

            return ProviderResult(
                status=status,
                details=content.get("details", {}),
                raw_evidence=content.get("raw_evidence"),
                source=content.get("source", self.name),
                as_of=content.get("as_of", datetime.date.today().isoformat()),
                error_message=content.get("error_message"),
            )
        except Exception as exc:
            return ProviderResult(
                status=ProviderStatus.ERROR,
                details={},
                raw_evidence=None,
                source=self.name,
                as_of=datetime.date.today().isoformat(),
                error_message=f"Error parsing fixture file '{target_file.name}': {exc}",
            )
