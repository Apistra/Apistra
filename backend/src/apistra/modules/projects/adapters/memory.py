"""Thread-safe in-memory project adapter for local development and tests."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from uuid import UUID

from apistra.modules.projects.domain import Project, ProjectAuditEvent, ProjectStatus


class InMemoryProjectStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._projects: dict[UUID, Project] = {}
        self._idempotency: dict[tuple[UUID, str], tuple[str, UUID]] = {}
        self.audit_events: list[ProjectAuditEvent] = []

    def create(
        self, project, event, idempotency_key, request_fingerprint
    ) -> tuple[Project | None, str | None]:
        with self._lock:
            idempotency = self._idempotency.get((project.owner_administrator_id, idempotency_key))
            if idempotency:
                fingerprint, project_id = idempotency
                if fingerprint != request_fingerprint:
                    return None, "idempotency"
                return self._projects[project_id], None
            if any(
                existing.owner_administrator_id == project.owner_administrator_id
                and existing.key == project.key
                for existing in self._projects.values()
            ):
                return None, "key"
            self._projects[project.id] = project
            self._idempotency[(project.owner_administrator_id, idempotency_key)] = (
                request_fingerprint,
                project.id,
            )
            self.audit_events.append(event)
            return project, None

    def list_for_owner(self, owner_id: UUID) -> list[Project]:
        with self._lock:
            return sorted(
                (
                    project
                    for project in self._projects.values()
                    if project.owner_administrator_id == owner_id
                ),
                key=lambda project: (project.key, str(project.id)),
            )

    def get_for_owner(self, owner_id: UUID, project_id: UUID) -> Project | None:
        with self._lock:
            project = self._projects.get(project_id)
            return project if project and project.owner_administrator_id == owner_id else None

    def update(
        self, owner_id, project_id, expected_version, name, key, updated_at, event
    ) -> tuple[Project | None, str | None]:
        with self._lock:
            current = self.get_for_owner(owner_id, project_id)
            if current is None:
                return None, "not_found"
            if current.version != expected_version or current.status is ProjectStatus.ARCHIVED:
                return None, "version"
            if any(
                item.owner_administrator_id == owner_id
                and item.id != project_id
                and item.key == key
                for item in self._projects.values()
            ):
                return None, "key"
            updated = replace(
                current,
                name=name,
                key=key,
                version=current.version + 1,
                updated_at=updated_at,
            )
            self._projects[project_id] = updated
            self.audit_events.append(replace(event, created_at=updated_at, project_key=key))
            return updated, None

    def archive(
        self, owner_id, project_id, expected_version, updated_at, event
    ) -> tuple[Project | None, str | None]:
        with self._lock:
            current = self.get_for_owner(owner_id, project_id)
            if current is None:
                return None, "not_found"
            if current.version != expected_version or current.status is ProjectStatus.ARCHIVED:
                return None, "version"
            archived = replace(
                current,
                status=ProjectStatus.ARCHIVED,
                version=current.version + 1,
                updated_at=updated_at,
            )
            self._projects[project_id] = archived
            self.audit_events.append(replace(event, created_at=updated_at))
            return archived, None
