"""Persistence boundary for approval policy decisions."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.policies.domain import ApprovalException, PolicyAuditEvent


class PolicyStore(Protocol):
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
