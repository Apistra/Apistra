"""Domain model for isolated Administrator-owned projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ProjectErrorCode(StrEnum):
    INVALID_INPUT = "project.invalid_input"
    NOT_FOUND = "project.not_found"
    KEY_CONFLICT = "project.key_conflict"
    VERSION_CONFLICT = "project.version_conflict"
    IDEMPOTENCY_CONFLICT = "project.idempotency_conflict"


@dataclass(frozen=True, slots=True)
class ProjectError:
    code: ProjectErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    owner_administrator_id: UUID
    name: str
    key: str
    status: ProjectStatus
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ProjectAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    project_key: str
    details: dict[str, Any] = field(default_factory=dict)
