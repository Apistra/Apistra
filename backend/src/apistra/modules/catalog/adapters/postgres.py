"""PostgreSQL adapter for encrypted project secret references."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.catalog.domain import (
    EncryptedSecretEnvelope,
    SecretAuditEvent,
    SecretReference,
    SecretStatus,
)

type MappingRow = dict[str, Any]
type MappingCursor = psycopg.Cursor[MappingRow]


class PostgresSecretStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create(
        self,
        reference: SecretReference,
        event: SecretAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[SecretReference | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                replay = self._replay(
                    cursor,
                    reference.owner_administrator_id,
                    reference.project_id,
                    idempotency_key,
                    request_fingerprint,
                )
                if replay is not None:
                    return replay
                cursor.execute(
                    """
                    INSERT INTO secret_references
                        (id, owner_administrator_id, project_id, name, purpose, status,
                         version, envelope_format_version, key_id, nonce, ciphertext,
                         created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        reference.id,
                        reference.owner_administrator_id,
                        reference.project_id,
                        reference.name,
                        reference.purpose,
                        reference.status,
                        reference.version,
                        reference.envelope.format_version,
                        reference.envelope.key_id,
                        reference.envelope.nonce,
                        reference.envelope.ciphertext,
                        reference.created_at,
                        reference.updated_at,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO secret_idempotency
                        (owner_administrator_id, project_id, idempotency_key,
                         request_fingerprint, secret_reference_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        reference.owner_administrator_id,
                        reference.project_id,
                        idempotency_key,
                        request_fingerprint,
                        reference.id,
                        reference.created_at,
                    ),
                )
                self._insert_event(cursor, event)
        except errors.UniqueViolation as error:
            if error.diag.constraint_name == "secret_references_owner_project_name_unique":
                return None, "name"
            if error.diag.constraint_name == "secret_idempotency_pkey":
                return self._replay_after_race(reference, idempotency_key, request_fingerprint)
            raise
        return reference, None

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[SecretReference]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                f"{self._select()} WHERE owner_administrator_id = %s AND project_id = %s "
                "ORDER BY name, id",
                (owner_id, project_id),
            )
            return [self._reference(row) for row in cursor.fetchall()]

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> SecretReference | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            return self._get(cursor, owner_id, project_id, reference_id)

    def replace(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        envelope: EncryptedSecretEnvelope,
        updated_at: datetime,
        event: SecretAuditEvent,
    ) -> tuple[SecretReference | None, str | None]:
        return self._transition(
            owner_id,
            project_id,
            reference_id,
            expected_version,
            updated_at,
            event,
            envelope,
        )

    def revoke(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: SecretAuditEvent,
    ) -> tuple[SecretReference | None, str | None]:
        return self._transition(
            owner_id,
            project_id,
            reference_id,
            expected_version,
            updated_at,
            event,
            None,
        )

    def list_audit_for_owner(self, owner_id: UUID) -> list[SecretAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT e.id, e.event_type, e.created_at, e.correlation_id,
                       e.actor_id, e.actor_username, e.project_id,
                       e.secret_reference_id, e.details
                FROM secret_audit_events AS e
                JOIN projects AS p
                  ON p.id = e.project_id AND p.owner_administrator_id = %s
                ORDER BY e.created_at DESC, e.id DESC
                """,
                (owner_id,),
            )
            return [
                SecretAuditEvent(
                    id=row["id"],
                    event_type=row["event_type"],
                    created_at=row["created_at"],
                    correlation_id=row["correlation_id"],
                    actor_id=row["actor_id"],
                    actor_username=row["actor_username"],
                    project_id=row["project_id"],
                    secret_reference_id=row["secret_reference_id"],
                    details=row["details"],
                )
                for row in cursor.fetchall()
            ]

    def _transition(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: SecretAuditEvent,
        envelope: EncryptedSecretEnvelope | None,
    ) -> tuple[SecretReference | None, str | None]:
        assignment = (
            "envelope_format_version = %s, key_id = %s, nonce = %s, ciphertext = %s,"
            if envelope
            else "status = 'REVOKED',"
        )
        envelope_values: tuple[object, ...] = (
            (
                envelope.format_version,
                envelope.key_id,
                envelope.nonce,
                envelope.ciphertext,
            )
            if envelope
            else ()
        )
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                f"""
                UPDATE secret_references
                SET {assignment} version = version + 1, updated_at = %s
                WHERE id = %s AND owner_administrator_id = %s AND project_id = %s
                  AND version = %s AND status = 'ACTIVE'
                RETURNING id, owner_administrator_id, project_id, name, purpose, status,
                          version, envelope_format_version, key_id, nonce, ciphertext,
                          created_at, updated_at
                """,  # noqa: S608 - assignment is selected from a fixed internal allowlist
                (
                    *envelope_values,
                    updated_at,
                    reference_id,
                    owner_id,
                    project_id,
                    expected_version,
                ),
            )
            row = cursor.fetchone()
            if not row:
                return None, self._owned_conflict(cursor, owner_id, project_id, reference_id)
            self._insert_event(cursor, event, created_at=updated_at)
            return self._reference(row), None

    def _replay_after_race(
        self,
        reference: SecretReference,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[SecretReference | None, str | None]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            replay = self._replay(
                cursor,
                reference.owner_administrator_id,
                reference.project_id,
                idempotency_key,
                request_fingerprint,
            )
            return replay or (None, "idempotency")

    def _replay(
        self,
        cursor: MappingCursor,
        owner_id: UUID,
        project_id: UUID,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[SecretReference | None, str | None] | None:
        cursor.execute(
            """
            SELECT request_fingerprint, secret_reference_id
            FROM secret_idempotency
            WHERE owner_administrator_id = %s AND project_id = %s AND idempotency_key = %s
            """,
            (owner_id, project_id, idempotency_key),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            return None, "idempotency"
        return self._get(cursor, owner_id, project_id, row["secret_reference_id"]), None

    @staticmethod
    def _owned_conflict(
        cursor: MappingCursor, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> str:
        cursor.execute(
            """
            SELECT version, status FROM secret_references
            WHERE id = %s AND owner_administrator_id = %s AND project_id = %s
            """,
            (reference_id, owner_id, project_id),
        )
        return "version" if cursor.fetchone() else "not_found"

    def _get(
        self, cursor: MappingCursor, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> SecretReference | None:
        cursor.execute(
            f"{self._select()} WHERE id = %s AND owner_administrator_id = %s AND project_id = %s",
            (reference_id, owner_id, project_id),
        )
        row = cursor.fetchone()
        return self._reference(row) if row else None

    @staticmethod
    def _select() -> str:
        return (
            "SELECT id, owner_administrator_id, project_id, name, purpose, status, version, "
            "envelope_format_version, key_id, nonce, ciphertext, created_at, updated_at "
            "FROM secret_references"
        )

    @staticmethod
    def _reference(row: MappingRow) -> SecretReference:
        return SecretReference(
            id=row["id"],
            owner_administrator_id=row["owner_administrator_id"],
            project_id=row["project_id"],
            name=row["name"],
            purpose=row["purpose"],
            status=SecretStatus(row["status"]),
            version=row["version"],
            envelope=EncryptedSecretEnvelope(
                format_version=row["envelope_format_version"],
                key_id=row["key_id"],
                nonce=bytes(row["nonce"]),
                ciphertext=bytes(row["ciphertext"]),
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _insert_event(
        cursor: MappingCursor,
        event: SecretAuditEvent,
        *,
        created_at: datetime | None = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO secret_audit_events
                (id, event_type, created_at, correlation_id, actor_id, actor_username,
                 project_id, secret_reference_id, details)
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
                event.secret_reference_id,
                Jsonb(event.details),
            ),
        )
