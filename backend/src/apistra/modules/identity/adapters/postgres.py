"""PostgreSQL identity adapter with bounded atomic state changes."""

from __future__ import annotations

from datetime import datetime

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.identity.domain import Administrator, AuditEvent, Session, SessionContext


class PostgresIdentityStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def bootstrap(
        self,
        administrator: Administrator,
        session: Session,
        audit_event: AuditEvent,
    ) -> bool:
        try:
            with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO identity_administrators
                        (id, installation_id, username, password_hash, created_at)
                    VALUES (%s, 'local', %s, %s, %s)
                    """,
                    (
                        administrator.id,
                        administrator.username,
                        administrator.password_hash,
                        administrator.created_at,
                    ),
                )
                self._insert_session(cursor, session)
                self._insert_audit_event(cursor, audit_event)
        except errors.UniqueViolation:
            return False
        return True

    def installation_has_administrator(self) -> bool:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM identity_administrators WHERE installation_id = 'local'
                )
                """
            )
            row = cursor.fetchone()
            return bool(row and row[0])

    def find_administrator(self, username: str) -> Administrator | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM identity_administrators
                WHERE username = %s
                """,
                (username,),
            )
            row = cursor.fetchone()
            return self._administrator(row) if row else None

    def create_session(self, session: Session, audit_event: AuditEvent) -> None:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            self._insert_session(cursor, session)
            self._insert_audit_event(cursor, audit_event)

    def find_session(self, token_hash: str) -> SessionContext | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.administrator_id,
                    s.token_hash,
                    s.csrf_hash,
                    s.created_at,
                    s.expires_at,
                    s.revoked_at,
                    a.username AS administrator_username
                FROM identity_sessions AS s
                JOIN identity_administrators AS a ON a.id = s.administrator_id
                WHERE s.token_hash = %s
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return SessionContext(
                session=Session(
                    id=row["id"],
                    administrator_id=row["administrator_id"],
                    token_hash=row["token_hash"],
                    csrf_hash=row["csrf_hash"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    revoked_at=row["revoked_at"],
                ),
                administrator_username=row["administrator_username"],
            )

    def revoke_session(
        self,
        token_hash: str,
        csrf_hash: str,
        revoked_at: datetime,
        audit_event: AuditEvent,
    ) -> bool:
        with psycopg.connect(self._dsn) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE identity_sessions
                SET revoked_at = %s
                WHERE token_hash = %s AND csrf_hash = %s AND revoked_at IS NULL
                """,
                (revoked_at, token_hash, csrf_hash),
            )
            if cursor.rowcount != 1:
                return False
            self._insert_audit_event(cursor, audit_event)
            return True

    @staticmethod
    def _administrator(row: dict) -> Administrator:
        return Administrator(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _insert_session(cursor, session: Session) -> None:
        cursor.execute(
            """
            INSERT INTO identity_sessions
                (id, administrator_id, token_hash, csrf_hash, created_at, expires_at, revoked_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session.id,
                session.administrator_id,
                session.token_hash,
                session.csrf_hash,
                session.created_at,
                session.expires_at,
                session.revoked_at,
            ),
        )

    @staticmethod
    def _insert_audit_event(cursor, event: AuditEvent) -> None:
        cursor.execute(
            """
            INSERT INTO identity_audit_events
                (id, event_type, created_at, correlation_id, actor_id,
                 actor_username, subject_id, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event.id,
                event.event_type,
                event.created_at,
                event.correlation_id,
                event.actor_id,
                event.actor_username,
                event.subject_id,
                Jsonb(event.details),
            ),
        )


def count_identity_rows(dsn: str) -> dict[str, int]:
    """Test/evidence helper that never returns credential or token material."""

    tables = {
        "administrators": "identity_administrators",
        "sessions": "identity_sessions",
        "audit_events": "identity_audit_events",
    }
    result: dict[str, int] = {}
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        for key, table in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed allowlist
            row = cursor.fetchone()
            result[key] = int(row[0]) if row else 0
    return result
