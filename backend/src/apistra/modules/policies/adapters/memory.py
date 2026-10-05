"""Thread-safe local policy store."""

from datetime import datetime
from threading import RLock
from uuid import UUID

from apistra.modules.policies.domain import ApprovalException, PolicyAuditEvent


class InMemoryPolicyStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._exceptions: dict[UUID, ApprovalException] = {}
        self.audit_events: list[PolicyAuditEvent] = []

    def add_exception(self, exception: ApprovalException) -> None:
        with self._lock:
            self._exceptions[exception.id] = exception

    def find_exact_exception(
        self,
        owner_id: UUID,
        project_id: UUID,
        tool_id: UUID,
        tool_version: int,
        action: str,
        scope: str,
        evaluated_at: datetime,
    ) -> ApprovalException | None:
        with self._lock:
            return next(
                (
                    item
                    for item in self._exceptions.values()
                    if item.owner_administrator_id == owner_id
                    and item.project_id == project_id
                    and item.tool_id == tool_id
                    and item.tool_version == tool_version
                    and item.action == action
                    and item.scope == scope
                    and item.active
                    and item.expires_at > evaluated_at
                ),
                None,
            )

    def record_event(self, event: PolicyAuditEvent) -> None:
        with self._lock:
            self.audit_events.append(event)

    def list_audit_for_owner(self, owner_id: UUID) -> list[PolicyAuditEvent]:
        return sorted(
            (event for event in self.audit_events if event.actor_id == owner_id),
            key=lambda event: (event.created_at, str(event.id)),
            reverse=True,
        )
