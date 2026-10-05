"""PostgreSQL adapter for exact approval exceptions and decision evidence."""

from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.policies.domain import ApprovalException, PolicyAuditEvent

type Row = dict[str, Any]


class PostgresPolicyStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def add_exception(self, exception: ApprovalException) -> None:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO policy_approval_exceptions
                (id, owner_administrator_id, project_id, tool_id, tool_version,
                 action, scope, expires_at, active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING""",
                (
                    exception.id,
                    exception.owner_administrator_id,
                    exception.project_id,
                    exception.tool_id,
                    exception.tool_version,
                    exception.action,
                    exception.scope,
                    exception.expires_at,
                    exception.active,
                ),
            )

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
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM policy_approval_exceptions
                WHERE owner_administrator_id=%s AND project_id=%s
                  AND tool_id=%s AND tool_version=%s AND action=%s AND scope=%s
                  AND active=TRUE AND expires_at>%s
                ORDER BY expires_at DESC, id DESC LIMIT 1""",
                (owner_id, project_id, tool_id, tool_version, action, scope, evaluated_at),
            )
            row = cursor.fetchone()
            return ApprovalException(**row) if row else None

    def record_event(self, event: PolicyAuditEvent) -> None:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO policy_audit_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
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

    def list_audit_for_owner(self, owner_id: UUID) -> list[PolicyAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM policy_audit_events
                WHERE actor_id=%s ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            )
            return [PolicyAuditEvent(**row) for row in cursor.fetchall()]
