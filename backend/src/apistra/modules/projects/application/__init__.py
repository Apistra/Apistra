"""Project lifecycle use cases with ownership and optimistic concurrency."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from apistra.modules.projects.domain import (
    Project,
    ProjectAuditEvent,
    ProjectError,
    ProjectErrorCode,
    ProjectStatus,
)
from apistra.modules.projects.ports import ProjectClock, ProjectStore

PROJECT_KEY_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,31}$")
MAXIMUM_NAME_LENGTH = 128
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128


@dataclass(frozen=True, slots=True)
class ProjectResult[T]:
    value: T | None = None
    error: ProjectError | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class ProjectService:
    def __init__(self, store: ProjectStore, clock: ProjectClock) -> None:
        self._store = store
        self._clock = clock

    def create(
        self,
        owner_id: UUID,
        actor_username: str,
        name: str,
        key: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProjectResult[Project]:
        normalized_name = name.strip()
        normalized_key = key.strip().upper()
        error = self._validate(normalized_name, normalized_key)
        if error:
            return ProjectResult(error=error)
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return self._invalid("Idempotency-Key must contain 1 to 128 characters.")
        now = self._clock.now()
        project = Project(
            id=uuid4(),
            owner_administrator_id=owner_id,
            name=normalized_name,
            key=normalized_key,
            status=ProjectStatus.ACTIVE,
            version=1,
            created_at=now,
            updated_at=now,
        )
        event = self._event("project.created", project, actor_username, correlation_id)
        fingerprint = hashlib.sha256(f"{normalized_name}\0{normalized_key}".encode()).hexdigest()
        stored, conflict = self._store.create(project, event, idempotency_key, fingerprint)
        if stored:
            return ProjectResult(value=stored)
        return ProjectResult(error=self._store_error(conflict))

    def list(self, owner_id: UUID) -> ProjectResult[list[Project]]:
        return ProjectResult(value=self._store.list_for_owner(owner_id))

    def get(self, owner_id: UUID, project_id: UUID) -> ProjectResult[Project]:
        project = self._store.get_for_owner(owner_id, project_id)
        if project is None:
            return self._not_found()
        return ProjectResult(value=project)

    def update(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        expected_version: int,
        name: str,
        key: str,
        correlation_id: str,
    ) -> ProjectResult[Project]:
        normalized_name = name.strip()
        normalized_key = key.strip().upper()
        error = self._validate(normalized_name, normalized_key)
        if error:
            return ProjectResult(error=error)
        current = self._store.get_for_owner(owner_id, project_id)
        if current is None:
            return self._not_found()
        event = self._event(
            "project.updated",
            current,
            actor_username,
            correlation_id,
            {"from_version": expected_version},
        )
        stored, conflict = self._store.update(
            owner_id,
            project_id,
            expected_version,
            normalized_name,
            normalized_key,
            self._clock.now(),
            event,
        )
        if stored:
            return ProjectResult(value=stored)
        return ProjectResult(error=self._store_error(conflict))

    def archive(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        expected_version: int,
        correlation_id: str,
    ) -> ProjectResult[Project]:
        current = self._store.get_for_owner(owner_id, project_id)
        if current is None:
            return self._not_found()
        event = self._event(
            "project.archived",
            current,
            actor_username,
            correlation_id,
            {"from_version": expected_version},
        )
        stored, conflict = self._store.archive(
            owner_id, project_id, expected_version, self._clock.now(), event
        )
        if stored:
            return ProjectResult(value=stored)
        return ProjectResult(error=self._store_error(conflict))

    @staticmethod
    def _validate(name: str, key: str) -> ProjectError | None:
        if not 1 <= len(name) <= MAXIMUM_NAME_LENGTH:
            return ProjectError(
                ProjectErrorCode.INVALID_INPUT,
                "Project name is required and may contain at most 128 characters.",
            )
        if not PROJECT_KEY_PATTERN.fullmatch(key):
            return ProjectError(
                ProjectErrorCode.INVALID_INPUT,
                "Project key must contain 2 to 32 uppercase letters, numbers, or hyphens.",
            )
        return None

    @staticmethod
    def _event(
        event_type: str,
        project: Project,
        actor_username: str,
        correlation_id: str,
        details: dict | None = None,
    ) -> ProjectAuditEvent:
        return ProjectAuditEvent(
            id=uuid4(),
            event_type=event_type,
            created_at=project.updated_at,
            correlation_id=correlation_id,
            actor_id=project.owner_administrator_id,
            actor_username=actor_username,
            project_id=project.id,
            project_key=project.key,
            details=details or {},
        )

    @staticmethod
    def _invalid(message: str) -> ProjectResult:
        return ProjectResult(error=ProjectError(ProjectErrorCode.INVALID_INPUT, message))

    @staticmethod
    def _not_found() -> ProjectResult:
        return ProjectResult(
            error=ProjectError(
                ProjectErrorCode.NOT_FOUND,
                "The project does not exist or you do not have access.",
            )
        )

    @classmethod
    def _store_error(cls, conflict: str | None) -> ProjectError:
        if conflict == "key":
            return ProjectError(ProjectErrorCode.KEY_CONFLICT, "Project key is already in use.")
        if conflict == "version":
            return ProjectError(
                ProjectErrorCode.VERSION_CONFLICT,
                "The project has changed. Reload it and try again.",
            )
        if conflict == "idempotency":
            return ProjectError(
                ProjectErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        return cls._not_found().error
