"""PostgreSQL adapter for exact approval exceptions and decision evidence."""

from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.policies.domain import (
    ApprovalException,
    LimitPolicyAuditEvent,
    LimitPolicyStatus,
    LimitPolicyVersion,
    PolicyAuditEvent,
)

type Row = dict[str, Any]
VERSION_FIELD = "version"
VERSION_CONFLICT = VERSION_FIELD


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

    def create_limit_policy_version(
        self,
        version: LimitPolicyVersion,
        event: LimitPolicyAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[LimitPolicyVersion | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                replay = self._limit_replay(cursor, version, idempotency_key)
                if replay:
                    if replay["request_fingerprint"] != request_fingerprint:
                        return None, "idempotency"
                    return self._get_limit_policy(
                        cursor,
                        version.owner_administrator_id,
                        version.project_id,
                        replay["policy_id"],
                        replay["policy_version"],
                    ), None
                if self._latest_limit_version(cursor, version) != expected_latest_version:
                    return None, VERSION_CONFLICT
                self._insert_limit_version(cursor, version)
                cursor.execute(
                    "INSERT INTO limit_policy_idempotency VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (
                        version.owner_administrator_id,
                        version.project_id,
                        idempotency_key,
                        request_fingerprint,
                        version.policy_id,
                        version.version,
                        version.created_at,
                    ),
                )
                self._insert_limit_event(cursor, event)
        except errors.UniqueViolation:
            return None, VERSION_CONFLICT
        return version, None

    @staticmethod
    def _limit_replay(
        cursor: psycopg.Cursor[Row], version: LimitPolicyVersion, key: str
    ) -> Row | None:
        cursor.execute(
            """SELECT request_fingerprint, policy_id, policy_version
            FROM limit_policy_idempotency
            WHERE owner_administrator_id=%s AND project_id=%s AND idempotency_key=%s""",
            (version.owner_administrator_id, version.project_id, key),
        )
        return cursor.fetchone()

    @staticmethod
    def _latest_limit_version(cursor: psycopg.Cursor[Row], version: LimitPolicyVersion) -> int:
        cursor.execute(
            """SELECT version FROM limit_policy_versions
            WHERE owner_administrator_id=%s AND project_id=%s AND policy_id=%s
            ORDER BY version DESC LIMIT 1 FOR UPDATE""",
            (version.owner_administrator_id, version.project_id, version.policy_id),
        )
        row = cursor.fetchone()
        return row[VERSION_FIELD] if row else 0

    @staticmethod
    def _insert_limit_version(cursor: psycopg.Cursor[Row], version: LimitPolicyVersion) -> None:
        cursor.execute(
            """INSERT INTO limit_policy_versions
            (policy_id, owner_administrator_id, project_id, version, status, name,
             maximum_duration_seconds, maximum_calls, maximum_tokens,
             maximum_cost_minor_units, currency, maximum_concurrency,
             rate_limit_requests, rate_limit_window_seconds,
             warning_threshold_percent, created_at, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                version.policy_id,
                version.owner_administrator_id,
                version.project_id,
                version.version,
                version.status,
                version.name,
                version.maximum_duration_seconds,
                version.maximum_calls,
                version.maximum_tokens,
                version.maximum_cost_minor_units,
                version.currency,
                version.maximum_concurrency,
                version.rate_limit_requests,
                version.rate_limit_window_seconds,
                version.warning_threshold_percent,
                version.created_at,
                version.created_by,
            ),
        )

    def list_latest_limit_policies(
        self, owner_id: UUID, project_id: UUID
    ) -> list[LimitPolicyVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT DISTINCT ON (policy_id) * FROM limit_policy_versions
                WHERE owner_administrator_id=%s AND project_id=%s
                ORDER BY policy_id, version DESC""",
                (owner_id, project_id),
            )
            return sorted(
                (self._limit_policy(row) for row in cursor.fetchall()),
                key=lambda item: (item.name, str(item.policy_id)),
            )

    def list_limit_policy_versions(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID
    ) -> list[LimitPolicyVersion]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM limit_policy_versions
                WHERE owner_administrator_id=%s AND project_id=%s AND policy_id=%s
                ORDER BY version DESC""",
                (owner_id, project_id, policy_id),
            )
            return [self._limit_policy(row) for row in cursor.fetchall()]

    def get_exact_limit_policy(
        self, owner_id: UUID, project_id: UUID, policy_id: UUID, version: int
    ) -> LimitPolicyVersion | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            return self._get_limit_policy(cursor, owner_id, project_id, policy_id, version)

    @staticmethod
    def _get_limit_policy(
        cursor: psycopg.Cursor[Row],
        owner_id: UUID,
        project_id: UUID,
        policy_id: UUID,
        version: int,
    ) -> LimitPolicyVersion | None:
        cursor.execute(
            """SELECT * FROM limit_policy_versions WHERE owner_administrator_id=%s
            AND project_id=%s AND policy_id=%s AND version=%s""",
            (owner_id, project_id, policy_id, version),
        )
        row = cursor.fetchone()
        return PostgresPolicyStore._limit_policy(row) if row else None

    @staticmethod
    def _limit_policy(row: Row) -> LimitPolicyVersion:
        return LimitPolicyVersion(
            policy_id=row["policy_id"],
            owner_administrator_id=row["owner_administrator_id"],
            project_id=row["project_id"],
            version=row[VERSION_FIELD],
            status=LimitPolicyStatus(row["status"]),
            name=row["name"],
            maximum_duration_seconds=row["maximum_duration_seconds"],
            maximum_calls=row["maximum_calls"],
            maximum_tokens=row["maximum_tokens"],
            maximum_cost_minor_units=row["maximum_cost_minor_units"],
            currency=row["currency"],
            maximum_concurrency=row["maximum_concurrency"],
            rate_limit_requests=row["rate_limit_requests"],
            rate_limit_window_seconds=row["rate_limit_window_seconds"],
            warning_threshold_percent=row["warning_threshold_percent"],
            created_at=row["created_at"],
            created_by=row["created_by"],
        )

    def record_limit_event(self, event: LimitPolicyAuditEvent) -> None:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            self._insert_limit_event(cursor, event)

    def publish_limit_policy_version(
        self,
        owner_id: UUID,
        project_id: UUID,
        policy_id: UUID,
        version: int,
        event: LimitPolicyAuditEvent,
    ) -> tuple[LimitPolicyVersion | None, str | None]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM limit_policy_versions
                WHERE owner_administrator_id=%s AND project_id=%s AND policy_id=%s
                ORDER BY version DESC LIMIT 1 FOR UPDATE""",
                (owner_id, project_id, policy_id),
            )
            latest = cursor.fetchone()
            if latest is None:
                return None, "unavailable"
            if latest[VERSION_FIELD] != version:
                return None, VERSION_CONFLICT
            if latest["status"] == LimitPolicyStatus.PUBLISHED:
                return self._limit_policy(latest), None
            cursor.execute(
                """UPDATE limit_policy_versions SET status='PUBLISHED'
                WHERE owner_administrator_id=%s AND project_id=%s
                  AND policy_id=%s AND version=%s AND status='DRAFT'
                RETURNING *""",
                (owner_id, project_id, policy_id, version),
            )
            published = cursor.fetchone()
            if published is None:
                return None, VERSION_CONFLICT
            self._insert_limit_event(cursor, event)
            return self._limit_policy(published), None

    @staticmethod
    def _insert_limit_event(cursor: psycopg.Cursor[Any], event: LimitPolicyAuditEvent) -> None:
        cursor.execute(
            "INSERT INTO limit_policy_audit_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                event.id,
                event.event_type,
                event.created_at,
                event.correlation_id,
                event.actor_id,
                event.actor_username,
                event.project_id,
                event.policy_id,
                event.policy_version,
                Jsonb(event.details),
            ),
        )

    def list_limit_audit_for_owner(self, owner_id: UUID) -> list[LimitPolicyAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """SELECT * FROM limit_policy_audit_events
                WHERE actor_id=%s ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            )
            return [LimitPolicyAuditEvent(**row) for row in cursor.fetchall()]

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
