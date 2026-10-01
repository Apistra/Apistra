"""PostgreSQL adapter for isolated project lifecycle operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.projects.domain import (
    Project,
    ProjectAuditEvent,
    ProjectStatus,
)


class PostgresProjectStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create(
        self,
        project: Project,
        event: ProjectAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[Project | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(
                    """
                    SELECT request_fingerprint, project_id
                    FROM project_idempotency
                    WHERE owner_administrator_id = %s AND idempotency_key = %s
                    """,
                    (project.owner_administrator_id, idempotency_key),
                )
                replay = cursor.fetchone()
                if replay:
                    if replay["request_fingerprint"] != request_fingerprint:
                        return None, "idempotency"
                    return (
                        self._get(
                            cursor,
                            project.owner_administrator_id,
                            replay["project_id"],
                        ),
                        None,
                    )
                cursor.execute(
                    """
                    INSERT INTO projects
                        (id, owner_administrator_id, name, project_key, status,
                         version, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        project.id,
                        project.owner_administrator_id,
                        project.name,
                        project.key,
                        project.status,
                        project.version,
                        project.created_at,
                        project.updated_at,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO project_idempotency
                        (owner_administrator_id, idempotency_key,
                         request_fingerprint, project_id, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        project.owner_administrator_id,
                        idempotency_key,
                        request_fingerprint,
                        project.id,
                        project.created_at,
                    ),
                )
                self._insert_event(cursor, event)
        except errors.UniqueViolation as error:
            constraint = error.diag.constraint_name
            if constraint == "projects_owner_key_unique":
                return None, "key"
            if constraint == "project_idempotency_pkey":
                return self._replay_after_race(
                    project.owner_administrator_id,
                    idempotency_key,
                    request_fingerprint,
                )
            raise
        return project, None

    def list_for_owner(self, owner_id: UUID) -> list[Project]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT id, owner_administrator_id, name, project_key, status,
                       version, created_at, updated_at
                FROM projects
                WHERE owner_administrator_id = %s
                ORDER BY project_key, id
                """,
                (owner_id,),
            )
            return [self._project(row) for row in cursor.fetchall()]

    def get_for_owner(self, owner_id: UUID, project_id: UUID) -> Project | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            return self._get(cursor, owner_id, project_id)

    def update(
        self,
        owner_id: UUID,
        project_id: UUID,
        expected_version: int,
        name: str,
        key: str,
        updated_at: datetime,
        event: ProjectAuditEvent,
    ) -> tuple[Project | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(
                    """
                    UPDATE projects
                    SET name = %s, project_key = %s, version = version + 1,
                        updated_at = %s
                    WHERE id = %s AND owner_administrator_id = %s
                      AND version = %s AND status = 'ACTIVE'
                    RETURNING id, owner_administrator_id, name, project_key,
                              status, version, created_at, updated_at
                    """,
                    (name, key, updated_at, project_id, owner_id, expected_version),
                )
                row = cursor.fetchone()
                if not row:
                    return None, self._owned_conflict(cursor, owner_id, project_id)
                self._insert_event(cursor, event, created_at=updated_at, project_key=key)
                return self._project(row), None
        except errors.UniqueViolation as error:
            if error.diag.constraint_name == "projects_owner_key_unique":
                return None, "key"
            raise

    def archive(
        self,
        owner_id: UUID,
        project_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: ProjectAuditEvent,
    ) -> tuple[Project | None, str | None]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                UPDATE projects
                SET status = 'ARCHIVED', version = version + 1, updated_at = %s
                WHERE id = %s AND owner_administrator_id = %s
                  AND version = %s AND status = 'ACTIVE'
                RETURNING id, owner_administrator_id, name, project_key,
                          status, version, created_at, updated_at
                """,
                (updated_at, project_id, owner_id, expected_version),
            )
            row = cursor.fetchone()
            if not row:
                return None, self._owned_conflict(cursor, owner_id, project_id)
            self._insert_event(cursor, event, created_at=updated_at)
            return self._project(row), None

    def _replay_after_race(
        self, owner_id: UUID, idempotency_key: str, fingerprint: str
    ) -> tuple[Project | None, str | None]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT request_fingerprint, project_id
                FROM project_idempotency
                WHERE owner_administrator_id = %s AND idempotency_key = %s
                """,
                (owner_id, idempotency_key),
            )
            replay = cursor.fetchone()
            if not replay or replay["request_fingerprint"] != fingerprint:
                return None, "idempotency"
            return self._get(cursor, owner_id, replay["project_id"]), None

    @staticmethod
    def _owned_conflict(cursor, owner_id: UUID, project_id: UUID) -> str:
        cursor.execute(
            "SELECT version, status FROM projects WHERE id = %s AND owner_administrator_id = %s",
            (project_id, owner_id),
        )
        return "version" if cursor.fetchone() else "not_found"

    @staticmethod
    def _get(cursor, owner_id: UUID, project_id: UUID) -> Project | None:
        cursor.execute(
            """
            SELECT id, owner_administrator_id, name, project_key, status,
                   version, created_at, updated_at
            FROM projects
            WHERE id = %s AND owner_administrator_id = %s
            """,
            (project_id, owner_id),
        )
        row = cursor.fetchone()
        return PostgresProjectStore._project(row) if row else None

    @staticmethod
    def _project(row: dict) -> Project:
        return Project(
            id=row["id"],
            owner_administrator_id=row["owner_administrator_id"],
            name=row["name"],
            key=row["project_key"],
            status=ProjectStatus(row["status"]),
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _insert_event(
        cursor,
        event: ProjectAuditEvent,
        *,
        created_at: datetime | None = None,
        project_key: str | None = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO project_audit_events
                (id, event_type, created_at, correlation_id, actor_id,
                 actor_username, project_id, project_key, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event.id,
                event.event_type,
                created_at or event.created_at,
                event.correlation_id,
                event.actor_id,
                event.actor_username,
                event.project_id,
                project_key or event.project_key,
                Jsonb(event.details),
            ),
        )


def count_project_rows(dsn: str) -> dict[str, int]:
    tables = {
        "projects": "projects",
        "idempotency": "project_idempotency",
        "audit_events": "project_audit_events",
    }
    result: dict[str, int] = {}
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        for key, table in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed allowlist
            row = cursor.fetchone()
            result[key] = int(row[0]) if row else 0
    return result
