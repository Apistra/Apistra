"""Framework-independent types for immutable agent versions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class AgentVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class AgentErrorCode(StrEnum):
    INVALID_INPUT = "agent.invalid_input"
    UNAVAILABLE = "agent.unavailable"
    VERSION_CONFLICT = "agent.version_conflict"
    IDEMPOTENCY_CONFLICT = "agent.idempotency_conflict"


@dataclass(frozen=True, slots=True)
class VersionReference:
    id: UUID
    version: int


@dataclass(frozen=True, slots=True)
class AgentVersion:
    agent_id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    version: int
    status: AgentVersionStatus
    name: str
    instructions: str
    primary_endpoint: VersionReference
    fallback_endpoint: VersionReference | None
    tool_versions: tuple[VersionReference, ...]
    limits_policy_version: VersionReference | None
    created_at: datetime
    created_by: UUID

    def ordered_endpoints(self) -> tuple[VersionReference, ...]:
        """Return the only endpoints a runtime is allowed to select."""

        return (
            (self.primary_endpoint, self.fallback_endpoint)
            if self.fallback_endpoint
            else (self.primary_endpoint,)
        )


@dataclass(frozen=True, slots=True)
class AgentError:
    code: AgentErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class AgentAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    agent_id: UUID
    agent_version: int
    details: dict[str, Any] = field(default_factory=dict)
