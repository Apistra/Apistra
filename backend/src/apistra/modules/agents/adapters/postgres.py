"""PostgreSQL adapter for immutable agent versions."""

from typing import Any
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.agents.domain import (
    AgentAuditEvent,
    AgentVersion,
    AgentVersionStatus,
    VersionReference,
)

type Row = dict[str, Any]
type MappingCursor = psycopg.Cursor[Row]
FIELD_VERSION = "version"  # noqa: WPS226 - shared persisted-field name


class PostgresAgentStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create_version(
        self,
        version: AgentVersion,
        event: AgentAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[AgentVersion | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(
                    """SELECT request_fingerprint, agent_id, agent_version
                    FROM agent_idempotency
                    WHERE owner_administrator_id=%s AND project_id=%s
                      AND idempotency_key=%s""",
                    (version.owner_administrator_id, version.project_id, idempotency_key),
                )
                replay = cursor.fetchone()
                if replay:
                    if replay["request_fingerprint"] != request_fingerprint:
                        return None, "idempotency"
                    return self._get(
                        cursor,
                        version.owner_administrator_id,
                        version.project_id,
                        replay["agent_id"],
                        replay["agent_version"],
                    ), None
                cursor.execute(
                    """SELECT version
                    FROM agent_versions
                    WHERE owner_administrator_id=%s AND project_id=%s AND agent_id=%s
                    ORDER BY version DESC LIMIT 1 FOR UPDATE""",
                    (version.owner_administrator_id, version.project_id, version.agent_id),
                )
                latest = cursor.fetchone()
                latest_version = latest[FIELD_VERSION] if latest else 0
                if latest_version != expected_latest_version:
                    return None, "version"
                cursor.execute(
                    """INSERT INTO agent_versions
                    (agent_id, owner_administrator_id, project_id, version, status, name,
                     instructions, primary_endpoint_id, primary_endpoint_version,
                     fallback_endpoint_id, fallback_endpoint_version, tool_versions,
                     limits_policy_id, limits_policy_version, created_at, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        version.agent_id,
                        version.owner_administrator_id,
                        version.project_id,
                        version.version,
                        version.status,
                        version.name,
                        version.instructions,
                        version.primary_endpoint.id,
                        version.primary_endpoint.version,
                        version.fallback_endpoint.id if version.fallback_endpoint else None,
                        version.fallback_endpoint.version if version.fallback_endpoint else None,
                        Jsonb(
                            [
                                {"id": str(item.id), "version": item.version}
                                for item in version.tool_versions
                            ]
                        ),
                        version.limits_policy_version.id if version.limits_policy_version else None,
                        version.limits_policy_version.version
                        if version.limits_policy_version
                        else None,
                        version.created_at,
                        version.created_by,
                    ),
                )
                cursor.execute(
                    "INSERT INTO agent_idempotency VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (
                        version.owner_administrator_id,
                        version.project_id,
                        idempotency_key,
                        request_fingerprint,
                        version.agent_id,
                        version.version,
                        version.created_at,
                    ),
                )
                cursor.execute(
                    "INSERT INTO agent_audit_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        event.id,
                        event.event_type,
                        event.created_at,
                        event.correlation_id,
                        event.actor_id,
                        event.actor_username,
                        event.project_id,
                        event.agent_id,
                        event.agent_version,
                        Jsonb(event.details),
                    ),
                )
        except errors.UniqueViolation:
            return None, "version"
        return version, None

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[AgentVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT DISTINCT ON (agent_id) * FROM agent_versions
                WHERE owner_administrator_id=%s AND project_id=%s
                ORDER BY agent_id, version DESC""",
                (owner_id, project_id),
            )
            return sorted(
                (self._version(row) for row in cursor.fetchall()),
                key=lambda item: (item.name, str(item.agent_id)),
            )

    def list_versions(self, owner_id: UUID, project_id: UUID, agent_id: UUID) -> list[AgentVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM agent_versions
                WHERE owner_administrator_id=%s AND project_id=%s AND agent_id=%s
                ORDER BY version DESC""",
                (owner_id, project_id, agent_id),
            )
            return [self._version(row) for row in cursor.fetchall()]

    def list_audit_for_owner(self, owner_id: UUID) -> list[AgentAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM agent_audit_events
                WHERE actor_id=%s ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            )
            return [AgentAuditEvent(**row) for row in cursor.fetchall()]

    @staticmethod
    def _get(
        cursor: MappingCursor,
        owner_id: UUID,
        project_id: UUID,
        agent_id: UUID,
        version: int,
    ) -> AgentVersion | None:
        cursor.execute(
            """SELECT * FROM agent_versions
            WHERE owner_administrator_id=%s AND project_id=%s
              AND agent_id=%s AND version=%s""",
            (owner_id, project_id, agent_id, version),
        )
        row = cursor.fetchone()
        return PostgresAgentStore._version(row) if row else None

    @staticmethod
    def _version(row: Row) -> AgentVersion:
        fallback = (
            VersionReference(row["fallback_endpoint_id"], row["fallback_endpoint_version"])
            if row["fallback_endpoint_id"]
            else None
        )
        policy = (
            VersionReference(row["limits_policy_id"], row["limits_policy_version"])
            if row["limits_policy_id"]
            else None
        )
        return AgentVersion(
            agent_id=row["agent_id"],
            owner_administrator_id=row["owner_administrator_id"],
            project_id=row["project_id"],
            version=row[FIELD_VERSION],
            status=AgentVersionStatus(row["status"]),
            name=row["name"],
            instructions=row["instructions"],
            primary_endpoint=VersionReference(
                row["primary_endpoint_id"], row["primary_endpoint_version"]
            ),
            fallback_endpoint=fallback,
            tool_versions=tuple(
                VersionReference(UUID(item["id"]), item[FIELD_VERSION])
                for item in row["tool_versions"]
            ),
            limits_policy_version=policy,
            created_at=row["created_at"],
            created_by=row["created_by"],
        )
