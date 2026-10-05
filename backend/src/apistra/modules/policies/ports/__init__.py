"""Persistence boundary for approval policy decisions."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.policies.domain import (
    ApprovalException,
    LimitPolicyAuditEvent,
    LimitPolicyVersion,
    PolicyAuditEvent,
)


class PolicyStore(Protocol):
    def create_limit_policy_version(
        self,
        version: LimitPolicyVersion,
        event: LimitPolicyAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[LimitPolicyVersion | None, str | None]: ...

    def list_latest_limit_policies(
        self, owner_id: UUID, project_id: UUID
    ) -> list[LimitPolicyVersion]: ...

    def list_limit_policy_versions(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID
    ) -> list[LimitPolicyVersion]: ...

    def get_exact_limit_policy(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID, version: int
    ) -> LimitPolicyVersion | None: ...

    def publish_limit_policy_version(
        self,
        owner_id: UUID,
        project_id: UUID,
        policy_id: UUID,
        version: int,
        event: LimitPolicyAuditEvent,
    ) -> tuple[LimitPolicyVersion | None, str | None]: ...

    def record_limit_event(self, event: LimitPolicyAuditEvent) -> None: ...

    def list_limit_audit_for_owner(self, owner_id: UUID) -> list[LimitPolicyAuditEvent]: ...

    def add_exception(self, exception: ApprovalException) -> None: ...

    def find_exact_exception(
        self,
        owner_id: UUID,
        project_id: UUID,
        tool_id: UUID,
        tool_version: int,
        action: str,
        scope: str,
        evaluated_at: datetime,
    ) -> ApprovalException | None: ...

    def record_event(self, event: PolicyAuditEvent) -> None: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[PolicyAuditEvent]: ...


class PolicyClock(Protocol):
    def now(self) -> datetime: ...
