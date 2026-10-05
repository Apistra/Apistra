"""PostgreSQL adapter for immutable governed tool versions."""

from typing import Any
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.catalog.domain.tools import (
    ToolAuditEvent,
    ToolVersion,
    ToolVersionStatus,
)

type Row = dict[str, Any]
type MappingCursor = psycopg.Cursor[Row]
VERSION_CONFLICT = "version"


class PostgresToolStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create_version(
        self,
        version: ToolVersion,
        event: ToolAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[ToolVersion | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                replay = self._replay(cursor, version, idempotency_key)
                if replay:
                    if replay["request_fingerprint"] != request_fingerprint:
                        return None, "idempotency"
                    return self._get(
                        cursor,
                        version.owner_administrator_id,
                        version.project_id,
                        replay["tool_id"],
                        replay["tool_version"],
                    ), None
                if self._latest_version(cursor, version) != expected_latest_version:
                    return None, VERSION_CONFLICT
                self._insert_version(cursor, version)
                cursor.execute(
                    "INSERT INTO tool_idempotency VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (
                        version.owner_administrator_id,
                        version.project_id,
                        idempotency_key,
                        request_fingerprint,
                        version.tool_id,
                        version.version,
                        version.created_at,
                    ),
                )
                cursor.execute(
                    "INSERT INTO tool_audit_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        event.id,
                        event.event_type,
                        event.created_at,
                        event.correlation_id,
                        event.actor_id,
                        event.actor_username,
                        event.project_id,
                        event.tool_id,
                        event.tool_version,
                        Jsonb(event.details),
                    ),
                )
        except errors.UniqueViolation:
            return None, VERSION_CONFLICT
        return version, None

    @staticmethod
    def _replay(cursor: MappingCursor, version: ToolVersion, idempotency_key: str) -> Row | None:
        cursor.execute(
            """SELECT request_fingerprint, tool_id, tool_version FROM tool_idempotency
            WHERE owner_administrator_id=%s AND project_id=%s AND idempotency_key=%s""",
            (version.owner_administrator_id, version.project_id, idempotency_key),
        )
        return cursor.fetchone()

    @staticmethod
    def _latest_version(cursor: MappingCursor, version: ToolVersion) -> int:
        cursor.execute(
            """SELECT version FROM tool_versions
            WHERE owner_administrator_id=%s AND project_id=%s AND tool_id=%s
            ORDER BY version DESC LIMIT 1 FOR UPDATE""",
            (version.owner_administrator_id, version.project_id, version.tool_id),
        )
        latest = cursor.fetchone()
        return latest["version"] if latest else 0

    @staticmethod
    def _insert_version(cursor: MappingCursor, version: ToolVersion) -> None:
        cursor.execute(
            """INSERT INTO tool_versions
            (tool_id, owner_administrator_id, project_id, version, status, name,
             description, input_schema, output_schema, effect_class, actions,
             created_at, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                version.tool_id,
                version.owner_administrator_id,
                version.project_id,
                version.version,
                version.status,
                version.name,
                version.description,
                Jsonb(version.input_schema),
                Jsonb(version.output_schema),
                version.effect_class,
                list(version.actions),
                version.created_at,
                version.created_by,
            ),
        )

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[ToolVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT DISTINCT ON (tool_id) * FROM tool_versions
                WHERE owner_administrator_id=%s AND project_id=%s
                ORDER BY tool_id, version DESC""",
                (owner_id, project_id),
            )
            return sorted(
                (self._version(row) for row in cursor.fetchall()),
                key=lambda item: (item.name, str(item.tool_id)),
            )

    def list_versions(self, owner_id: UUID, project_id: UUID, tool_id: UUID) -> list[ToolVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM tool_versions
                WHERE owner_administrator_id=%s AND project_id=%s AND tool_id=%s
                ORDER BY version DESC""",
                (owner_id, project_id, tool_id),
            )
            return [self._version(row) for row in cursor.fetchall()]

    def get_exact(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID, version: int
    ) -> ToolVersion | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            return self._get(cursor, owner_id, project_id, tool_id, version)

    def list_audit_for_owner(self, owner_id: UUID) -> list[ToolAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM tool_audit_events
                WHERE actor_id=%s ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            )
            return [ToolAuditEvent(**row) for row in cursor.fetchall()]

    @staticmethod
    def _get(
        cursor: MappingCursor,
        owner_id: UUID,
        project_id: UUID,
        tool_id: UUID,
        version: int,
    ) -> ToolVersion | None:
        cursor.execute(
            """SELECT * FROM tool_versions WHERE owner_administrator_id=%s
            AND project_id=%s AND tool_id=%s AND version=%s""",
            (owner_id, project_id, tool_id, version),
        )
        row = cursor.fetchone()
        return PostgresToolStore._version(row) if row else None

    @staticmethod
    def _version(row: Row) -> ToolVersion:
        return ToolVersion(
            tool_id=row["tool_id"],
            owner_administrator_id=row["owner_administrator_id"],
            project_id=row["project_id"],
            version=row["version"],
            status=ToolVersionStatus(row["status"]),
            name=row["name"],
            description=row["description"],
            input_schema=row["input_schema"],
            output_schema=row["output_schema"],
            effect_class=row["effect_class"],
            actions=tuple(row["actions"]),
            created_at=row["created_at"],
            created_by=row["created_by"],
        )
