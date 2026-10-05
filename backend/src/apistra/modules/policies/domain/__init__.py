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
    VERSION_CONFLICT = "policy.version_conflict"
    IDEMPOTENCY_CONFLICT = "policy.idempotency_conflict"


class LimitPolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class LimitDecision(StrEnum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    DENY = "DENY"


class BudgetAction(StrEnum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class LimitPolicyVersion:
    policy_id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    version: int
    status: LimitPolicyStatus
    name: str
    maximum_duration_seconds: int
    maximum_calls: int
    maximum_tokens: int
    maximum_cost_minor_units: int
    currency: str
    maximum_concurrency: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
    warning_threshold_percent: int | None
    created_at: datetime
    created_by: UUID


@dataclass(frozen=True, slots=True)
class LimitObservation:
    duration_seconds: int
    calls: int
    tokens: int
    cost_minor_units: int
    concurrency: int
    requests_in_window: int
    rate_window_seconds: int


@dataclass(frozen=True, slots=True)
class LimitBudgetDecision:
    decision: LimitDecision
    action: BudgetAction
    project_id: UUID
    policy_id: UUID
    policy_version: int
    violated_limits: tuple[str, ...]
    warned_limits: tuple[str, ...]
    effect_permitted: bool


@dataclass(frozen=True, slots=True)
class LimitPolicyAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    policy_id: UUID
    policy_version: int
    details: dict[str, Any] = field(default_factory=dict)


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
