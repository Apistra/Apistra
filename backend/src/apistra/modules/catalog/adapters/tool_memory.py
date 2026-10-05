"""Thread-safe local store for immutable governed tool versions."""

from threading import RLock
from uuid import UUID

from apistra.modules.catalog.domain.tools import ToolAuditEvent, ToolVersion


class InMemoryToolStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[tuple[UUID, int], ToolVersion] = {}
        self._idempotency: dict[tuple[UUID, UUID, str], tuple[str, UUID, int]] = {}
        self.audit_events: list[ToolAuditEvent] = []

    def create_version(
        self,
        version: ToolVersion,
        event: ToolAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[ToolVersion | None, str | None]:
        with self._lock:
            replay_key = (version.owner_administrator_id, version.project_id, idempotency_key)
            replay = self._idempotency.get(replay_key)
            if replay:
                fingerprint, tool_id, number = replay
                return (
                    (self._versions[(tool_id, number)], None)
                    if fingerprint == request_fingerprint
                    else (None, "idempotency")
                )
            current = self._latest(
                version.owner_administrator_id, version.project_id, version.tool_id
            )
            current_number = current.version if current else 0
            if current_number != expected_latest_version:
                return None, "version"
            self._versions[(version.tool_id, version.version)] = version
            self._idempotency[replay_key] = (
                request_fingerprint,
                version.tool_id,
                version.version,
            )
            self.audit_events.append(event)
            return version, None

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[ToolVersion]:
        with self._lock:
            tool_ids = {
                item.tool_id
                for item in self._versions.values()
                if item.owner_administrator_id == owner_id and item.project_id == project_id
            }
            latest = [self._latest(owner_id, project_id, tool_id) for tool_id in tool_ids]
            return sorted(
                (item for item in latest if item is not None),
                key=lambda item: (item.name, str(item.tool_id)),
            )

    def list_versions(self, owner_id: UUID, project_id: UUID, tool_id: UUID) -> list[ToolVersion]:
        with self._lock:
            return sorted(
                (
                    item
                    for item in self._versions.values()
                    if item.owner_administrator_id == owner_id
                    and item.project_id == project_id
                    and item.tool_id == tool_id
                ),
                key=lambda item: item.version,
                reverse=True,
            )

    def get_exact(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID, version: int
    ) -> ToolVersion | None:
        with self._lock:
            item = self._versions.get((tool_id, version))
            if item and item.owner_administrator_id == owner_id and item.project_id == project_id:
                return item
            return None

    def list_audit_for_owner(self, owner_id: UUID) -> list[ToolAuditEvent]:
        return sorted(
            (event for event in self.audit_events if event.actor_id == owner_id),
            key=lambda event: (event.created_at, str(event.id)),
            reverse=True,
        )

    def _latest(self, owner_id: UUID, project_id: UUID, tool_id: UUID) -> ToolVersion | None:
        matches = [
            item
            for item in self._versions.values()
            if item.owner_administrator_id == owner_id
            and item.project_id == project_id
            and item.tool_id == tool_id
        ]
        return max(matches, key=lambda item: item.version, default=None)
