"""Framework-independent approval policy types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class EffectClass(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class ApprovalDecision(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class PolicyErrorCode(StrEnum):
    INVALID_INPUT = "policy.invalid_input"
    UNAVAILABLE = "policy.unavailable"


@dataclass(frozen=True, slots=True)
class ApprovalException:
    id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    tool_id: UUID
    tool_version: int
    action: str
    scope: str
    expires_at: datetime
    active: bool


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: ApprovalDecision
    project_id: UUID
    tool_id: UUID
    tool_version: int
    action: str
    scope: str
    exception_id: UUID | None


@dataclass(frozen=True, slots=True)
class PolicyError:
    code: PolicyErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class PolicyAuditEvent:
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
