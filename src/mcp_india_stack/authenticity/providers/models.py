"""Models and status enumeration for registry providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    """Normalized status values emitted by registry verification providers."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ProviderResult:
    """Standard verification result returned by all registry providers.

    Adheres to Authenticity System A4 specifications.
    """

    status: ProviderStatus
    registry_status: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    raw_evidence: dict[str, Any] | None = None
    source: str = "Unknown Provider"
    as_of: str = ""
    error_message: str | None = None
    rate_limit_remaining: int | None = None

    def __post_init__(self) -> None:
        if self.registry_status is None:
            object.__setattr__(self, "registry_status", self.status.value)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a standard dictionary representation."""
        out: dict[str, Any] = {
            "status": self.status.value,
            "registry_status": self.registry_status or self.status.value,
            "details": self.details,
            "source": self.source,
            "as_of": self.as_of,
        }
        if self.raw_evidence is not None:
            out["raw_evidence"] = self.raw_evidence
        if self.error_message:
            out["error_message"] = self.error_message
        if self.rate_limit_remaining is not None:
            out["rate_limit_remaining"] = self.rate_limit_remaining
        return out
