"""Framework-independent contracts for immutable governed tool versions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ToolVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ToolErrorCode(StrEnum):
    INVALID_INPUT = "tool.invalid_input"
    UNAVAILABLE = "tool.unavailable"
    VERSION_CONFLICT = "tool.version_conflict"
    IDEMPOTENCY_CONFLICT = "tool.idempotency_conflict"


@dataclass(frozen=True, slots=True)
class ToolVersion:
    tool_id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    version: int
    status: ToolVersionStatus
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    effect_class: str
    actions: tuple[str, ...]
    created_at: datetime
    created_by: UUID


@dataclass(frozen=True, slots=True)
class ToolError:
    code: ToolErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class ToolAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    tool_id: UUID
    tool_version: int
    details: dict[str, Any] = field(default_factory=dict)
