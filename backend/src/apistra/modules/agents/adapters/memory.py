"""Thread-safe local store for immutable agent versions."""

from threading import RLock
from uuid import UUID

from apistra.modules.agents.domain import AgentAuditEvent, AgentVersion


class InMemoryAgentStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[tuple[UUID, int], AgentVersion] = {}
        self._idempotency: dict[tuple[UUID, UUID, str], tuple[str, UUID, int]] = {}
        self.audit_events: list[AgentAuditEvent] = []

    def create_version(
        self,
        version: AgentVersion,
        event: AgentAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[AgentVersion | None, str | None]:
        with self._lock:
            replay_key = (version.owner_administrator_id, version.project_id, idempotency_key)
            replay = self._idempotency.get(replay_key)
            if replay:
                fingerprint, agent_id, number = replay
                return (
                    (self._versions[(agent_id, number)], None)
                    if fingerprint == request_fingerprint
                    else (None, "idempotency")
                )
            current = self._latest(
                version.owner_administrator_id, version.project_id, version.agent_id
            )
            current_number = current.version if current else 0
            if current_number != expected_latest_version:
                return None, "version"
            self._versions[(version.agent_id, version.version)] = version
            self._idempotency[replay_key] = (
                request_fingerprint,
                version.agent_id,
                version.version,
            )
            self.audit_events.append(event)
            return version, None

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[AgentVersion]:
        with self._lock:
            agent_ids = {
                item.agent_id
                for item in self._versions.values()
                if item.owner_administrator_id == owner_id and item.project_id == project_id
            }
            latest = [self._latest(owner_id, project_id, agent_id) for agent_id in agent_ids]
            return sorted(
                (item for item in latest if item is not None),
                key=lambda item: (item.name, str(item.agent_id)),
            )

    def list_versions(self, owner_id: UUID, project_id: UUID, agent_id: UUID) -> list[AgentVersion]:
        with self._lock:
            return sorted(
                (
                    item
                    for item in self._versions.values()
                    if item.owner_administrator_id == owner_id
                    and item.project_id == project_id
                    and item.agent_id == agent_id
                ),
                key=lambda item: item.version,
                reverse=True,
            )

    def list_audit_for_owner(self, owner_id: UUID) -> list[AgentAuditEvent]:
        return sorted(
            (event for event in self.audit_events if event.actor_id == owner_id),
            key=lambda event: (event.created_at, str(event.id)),
            reverse=True,
        )

    def _latest(self, owner_id: UUID, project_id: UUID, agent_id: UUID) -> AgentVersion | None:
        matches = [
            item
            for item in self._versions.values()
            if item.owner_administrator_id == owner_id
            and item.project_id == project_id
            and item.agent_id == agent_id
        ]
        return max(matches, key=lambda item: item.version, default=None)
