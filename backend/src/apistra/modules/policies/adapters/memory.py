"""Thread-safe local policy store."""

from dataclasses import replace
from datetime import datetime
from threading import RLock
from uuid import UUID

from apistra.modules.policies.domain import (
    ApprovalException,
    LimitPolicyAuditEvent,
    LimitPolicyStatus,
    LimitPolicyVersion,
    PolicyAuditEvent,
)


class InMemoryPolicyStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._exceptions: dict[UUID, ApprovalException] = {}
        self._limit_versions: dict[tuple[UUID, int], LimitPolicyVersion] = {}
        self._limit_idempotency: dict[tuple[UUID, UUID, str], tuple[str, UUID, int]] = {}
        self.audit_events: list[PolicyAuditEvent] = []
        self.limit_audit_events: list[LimitPolicyAuditEvent] = []

    def create_limit_policy_version(
        self,
        version: LimitPolicyVersion,
        event: LimitPolicyAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[LimitPolicyVersion | None, str | None]:
        with self._lock:
            replay_key = (version.owner_administrator_id, version.project_id, idempotency_key)
            replay = self._limit_idempotency.get(replay_key)
            if replay:
                fingerprint, policy_id, number = replay
                return (
                    (self._limit_versions[(policy_id, number)], None)
                    if fingerprint == request_fingerprint
                    else (None, "idempotency")
                )
            current = self._latest_limit_policy(
                version.owner_administrator_id, version.project_id, version.policy_id
            )
            if (current.version if current else 0) != expected_latest_version:
                return None, "version"
            self._limit_versions[(version.policy_id, version.version)] = version
            self._limit_idempotency[replay_key] = (
                request_fingerprint,
                version.policy_id,
                version.version,
            )
            self.limit_audit_events.append(event)
            return version, None

    def list_latest_limit_policies(
        self, owner_id: UUID, project_id: UUID
    ) -> list[LimitPolicyVersion]:
        with self._lock:
            policy_ids = {
                item.policy_id
                for item in self._limit_versions.values()
                if item.owner_administrator_id == owner_id and item.project_id == project_id
            }
            values = [self._latest_limit_policy(owner_id, project_id, item) for item in policy_ids]
            return sorted(
                (item for item in values if item is not None),
                key=lambda item: (item.name, str(item.policy_id)),
            )

    def list_limit_policy_versions(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID
    ) -> list[LimitPolicyVersion]:
        with self._lock:
            return sorted(
                (
                    item
                    for item in self._limit_versions.values()
                    if item.owner_administrator_id == owner_id
                    and item.project_id == project_id
                    and item.policy_id == policy_id
                ),
                key=lambda item: item.version,
                reverse=True,
            )

    def get_exact_limit_policy(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID, version: int
    ) -> LimitPolicyVersion | None:
        with self._lock:
            item = self._limit_versions.get((policy_id, version))
            if item and item.owner_administrator_id == owner_id and item.project_id == project_id:
                return item
            return None

    def record_limit_event(self, event: LimitPolicyAuditEvent) -> None:
        with self._lock:
            self.limit_audit_events.append(event)

    def publish_limit_policy_version(
        self,
        owner_id: UUID,
        project_id: UUID,
        policy_id: UUID,
        version: int,
        event: LimitPolicyAuditEvent,
    ) -> tuple[LimitPolicyVersion | None, str | None]:
        with self._lock:
            current = self.get_exact_limit_policy(owner_id, project_id, policy_id, version)
            if current is None:
                return None, "unavailable"
            latest = self._latest_limit_policy(owner_id, project_id, policy_id)
            if latest is None or latest.version != version:
                return None, "version"
            if current.status is LimitPolicyStatus.PUBLISHED:
                return current, None
            published = replace(current, status=LimitPolicyStatus.PUBLISHED)
            self._limit_versions[(policy_id, version)] = published
            self.limit_audit_events.append(event)
            return published, None

    def list_limit_audit_for_owner(self, owner_id: UUID) -> list[LimitPolicyAuditEvent]:
        return sorted(
            (event for event in self.limit_audit_events if event.actor_id == owner_id),
            key=lambda event: (event.created_at, str(event.id)),
            reverse=True,
        )

    def _latest_limit_policy(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID
    ) -> LimitPolicyVersion | None:
        matches = [
            item
            for item in self._limit_versions.values()
            if item.owner_administrator_id == owner_id
            and item.project_id == project_id
            and item.policy_id == policy_id
        ]
        return max(matches, key=lambda item: item.version, default=None)

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
