"""PostgreSQL adapter for project-scoped model endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apistra.modules.catalog.domain.endpoints import (
    EndpointAuditEvent,
    EndpointPurpose,
    EndpointStatus,
    ModelEndpoint,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)

type MappingRow = dict[str, Any]
type MappingCursor = psycopg.Cursor[MappingRow]
ENDPOINT_COLUMNS = (
    "id, owner_administrator_id, project_id, name, purpose, provider_protocol, "
    "base_url, model_identifier, secret_reference_id, network_profile, status, "
    "version, last_probe_outcome, created_at, updated_at"
)


class PostgresEndpointStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def create(
        self,
        endpoint: ModelEndpoint,
        event: EndpointAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[ModelEndpoint | None, str | None]:
        try:
            with (
                psycopg.connect(self._dsn, row_factory=dict_row) as connection,
                connection.cursor() as cursor,
            ):
                replay = self._replay(
                    cursor,
                    endpoint.owner_administrator_id,
                    endpoint.project_id,
                    idempotency_key,
                    request_fingerprint,
                )
                if replay is not None:
                    return replay
                cursor.execute(
                    """
                    INSERT INTO model_endpoints
                        (id, owner_administrator_id, project_id, name, purpose,
                         provider_protocol, base_url, model_identifier,
                         secret_reference_id, network_profile, status, version,
                         last_probe_outcome, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        endpoint.id,
                        endpoint.owner_administrator_id,
                        endpoint.project_id,
                        endpoint.name,
                        endpoint.purpose,
                        endpoint.provider_protocol,
                        endpoint.base_url,
                        endpoint.model_identifier,
                        endpoint.secret_reference_id,
                        endpoint.network_profile,
                        endpoint.status,
                        endpoint.version,
                        endpoint.last_probe_outcome,
                        endpoint.created_at,
                        endpoint.updated_at,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO endpoint_idempotency
                        (owner_administrator_id, project_id, idempotency_key,
                         request_fingerprint, endpoint_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        endpoint.owner_administrator_id,
                        endpoint.project_id,
                        idempotency_key,
                        request_fingerprint,
                        endpoint.id,
                        endpoint.created_at,
                    ),
                )
                self._insert_event(cursor, event)
        except errors.UniqueViolation as error:
            if error.diag.constraint_name == "model_endpoints_owner_project_name_unique":
                return None, "name"
            if error.diag.constraint_name == "endpoint_idempotency_pkey":
                return self._replay_after_race(endpoint, idempotency_key, request_fingerprint)
            raise
        return endpoint, None

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[ModelEndpoint]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                f"{self._select()} WHERE owner_administrator_id = %s AND project_id = %s "
                "ORDER BY name, id",
                (owner_id, project_id),
            )
            return [self._endpoint(row) for row in cursor.fetchall()]

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, endpoint_id: UUID
    ) -> ModelEndpoint | None:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            return self._get(cursor, owner_id, project_id, endpoint_id)

    def record_probe(
        self,
        owner_id: UUID,
        project_id: UUID,
        endpoint_id: UUID,
        expected_version: int,
        outcome: ProbeOutcome,
        updated_at: datetime,
        event: EndpointAuditEvent,
    ) -> tuple[ModelEndpoint | None, str | None]:
        endpoint_status = (
            EndpointStatus.VERIFIED
            if outcome is ProbeOutcome.CONNECTION_VERIFIED
            else EndpointStatus.UNVERIFIED
        )
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                f"""
                UPDATE model_endpoints
                SET status = %s, last_probe_outcome = %s, version = version + 1, updated_at = %s
                WHERE id = %s AND owner_administrator_id = %s AND project_id = %s
                  AND version = %s
                RETURNING {self._columns()}
                """,  # noqa: S608 - columns are a fixed internal constant
                (
                    endpoint_status,
                    outcome,
                    updated_at,
                    endpoint_id,
                    owner_id,
                    project_id,
                    expected_version,
                ),
            )
            row = cursor.fetchone()
            if not row:
                return None, self._owned_conflict(cursor, owner_id, project_id, endpoint_id)
            self._insert_event(cursor, event, created_at=updated_at)
            return self._endpoint(row), None

    def list_audit_for_owner(self, owner_id: UUID) -> list[EndpointAuditEvent]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT e.id, e.event_type, e.created_at, e.correlation_id,
                       e.actor_id, e.actor_username, e.project_id, e.endpoint_id, e.details
                FROM endpoint_audit_events AS e
                JOIN projects AS p
                  ON p.id = e.project_id AND p.owner_administrator_id = %s
                ORDER BY e.created_at DESC, e.id DESC
                """,
                (owner_id,),
            )
            return [self._event(row) for row in cursor.fetchall()]

    def _replay_after_race(
        self, endpoint: ModelEndpoint, idempotency_key: str, request_fingerprint: str
    ) -> tuple[ModelEndpoint | None, str | None]:
        with (
            psycopg.connect(self._dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            replay = self._replay(
                cursor,
                endpoint.owner_administrator_id,
                endpoint.project_id,
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
    ) -> tuple[ModelEndpoint | None, str | None] | None:
        cursor.execute(
            """
            SELECT request_fingerprint, endpoint_id FROM endpoint_idempotency
            WHERE owner_administrator_id = %s AND project_id = %s AND idempotency_key = %s
            """,
            (owner_id, project_id, idempotency_key),
        )
        row = cursor.fetchone()
        if not row:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            return None, "idempotency"
        return self._get(cursor, owner_id, project_id, row["endpoint_id"]), None

    def _get(
        self, cursor: MappingCursor, owner_id: UUID, project_id: UUID, endpoint_id: UUID
    ) -> ModelEndpoint | None:
        cursor.execute(
            f"{self._select()} WHERE id = %s AND owner_administrator_id = %s AND project_id = %s",
            (endpoint_id, owner_id, project_id),
        )
        row = cursor.fetchone()
        return self._endpoint(row) if row else None

    @staticmethod
    def _owned_conflict(
        cursor: MappingCursor, owner_id: UUID, project_id: UUID, endpoint_id: UUID
    ) -> str:
        cursor.execute(
            """
            SELECT version FROM model_endpoints
            WHERE id = %s AND owner_administrator_id = %s AND project_id = %s
            """,
            (endpoint_id, owner_id, project_id),
        )
        return "version" if cursor.fetchone() else "not_found"

    @classmethod
    def _select(cls) -> str:
        return f"SELECT {cls._columns()} FROM model_endpoints"  # noqa: S608

    @staticmethod
    def _columns() -> str:
        return ENDPOINT_COLUMNS

    @staticmethod
    def _endpoint(row: MappingRow) -> ModelEndpoint:
        return ModelEndpoint(
            id=row["id"],
            owner_administrator_id=row["owner_administrator_id"],
            project_id=row["project_id"],
            name=row["name"],
            purpose=EndpointPurpose(row["purpose"]),
            provider_protocol=ProviderProtocol(row["provider_protocol"]),
            base_url=row["base_url"],
            model_identifier=row["model_identifier"],
            secret_reference_id=row["secret_reference_id"],
            network_profile=NetworkProfile(row["network_profile"]),
            status=EndpointStatus(row["status"]),
            version=row["version"],
            last_probe_outcome=(
                ProbeOutcome(row["last_probe_outcome"]) if row["last_probe_outcome"] else None
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _event(row: MappingRow) -> EndpointAuditEvent:
        return EndpointAuditEvent(
            id=row["id"],
            event_type=row["event_type"],
            created_at=row["created_at"],
            correlation_id=row["correlation_id"],
            actor_id=row["actor_id"],
            actor_username=row["actor_username"],
            project_id=row["project_id"],
            endpoint_id=row["endpoint_id"],
            details=row["details"],
        )

    @staticmethod
    def _insert_event(
        cursor: MappingCursor,
        event: EndpointAuditEvent,
        *,
        created_at: datetime | None = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO endpoint_audit_events
                (id, event_type, created_at, correlation_id, actor_id,
                 actor_username, project_id, endpoint_id, details)
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
                event.endpoint_id,
                Jsonb(event.details),
            ),
        )
