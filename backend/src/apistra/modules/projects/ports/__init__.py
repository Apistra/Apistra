"""Ports owned by the projects module."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.projects.domain import Project, ProjectAuditEvent


class ProjectClock(Protocol):
    def now(self) -> datetime: ...


class ProjectStore(Protocol):
    def create(
        self,
        project: Project,
        event: ProjectAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[Project | None, str | None]: ...

    def list_for_owner(self, owner_id: UUID) -> list[Project]: ...

    def get_for_owner(self, owner_id: UUID, project_id: UUID) -> Project | None: ...

    def update(
        self,
        owner_id: UUID,
        project_id: UUID,
        expected_version: int,
        name: str,
        key: str,
        updated_at: datetime,
        event: ProjectAuditEvent,
    ) -> tuple[Project | None, str | None]: ...

    def archive(
        self,
        owner_id: UUID,
        project_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: ProjectAuditEvent,
    ) -> tuple[Project | None, str | None]: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[ProjectAuditEvent]: ...
