"""Thread-safe in-memory endpoint store for tests and local development."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import RLock
from uuid import UUID

from apistra.modules.catalog.domain.endpoints import (
    EndpointAuditEvent,
    EndpointStatus,
    ModelEndpoint,
    ProbeOutcome,
)


class InMemoryEndpointStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._endpoints: dict[UUID, ModelEndpoint] = {}
        self._idempotency: dict[tuple[UUID, UUID, str], tuple[str, UUID]] = {}
        self.audit_events: list[EndpointAuditEvent] = []

    def create(
        self,
        endpoint: ModelEndpoint,
        event: EndpointAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[ModelEndpoint | None, str | None]:
        with self._lock:
            key = (endpoint.owner_administrator_id, endpoint.project_id, idempotency_key)
            replay = self._idempotency.get(key)
            if replay:
                fingerprint, endpoint_id = replay
                return (
                    (self._endpoints[endpoint_id], None)
                    if fingerprint == request_fingerprint
                    else (None, "idempotency")
                )
            if any(
                item.owner_administrator_id == endpoint.owner_administrator_id
                and item.project_id == endpoint.project_id
                and item.name == endpoint.name
                for item in self._endpoints.values()
            ):
                return None, "name"
            self._endpoints[endpoint.id] = endpoint
            self._idempotency[key] = (request_fingerprint, endpoint.id)
            self.audit_events.append(event)
            return endpoint, None

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[ModelEndpoint]:
        with self._lock:
            return sorted(
                (
                    item
                    for item in self._endpoints.values()
                    if item.owner_administrator_id == owner_id and item.project_id == project_id
                ),
                key=lambda item: (item.name, str(item.id)),
            )

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, endpoint_id: UUID
    ) -> ModelEndpoint | None:
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            if (
                endpoint
                and endpoint.owner_administrator_id == owner_id
                and endpoint.project_id == project_id
            ):
                return endpoint
            return None

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
        with self._lock:
            current = self.get_for_project(owner_id, project_id, endpoint_id)
            if current is None:
                return None, "not_found"
            if current.version != expected_version:
                return None, "version"
            updated = replace(
                current,
                status=(
                    EndpointStatus.VERIFIED
                    if outcome is ProbeOutcome.CONNECTION_VERIFIED
                    else EndpointStatus.UNVERIFIED
                ),
                last_probe_outcome=outcome,
                version=current.version + 1,
                updated_at=updated_at,
            )
            self._endpoints[endpoint_id] = updated
            self.audit_events.append(replace(event, created_at=updated_at))
            return updated, None

    def list_audit_for_owner(self, owner_id: UUID) -> list[EndpointAuditEvent]:
        with self._lock:
            return sorted(
                (event for event in self.audit_events if event.actor_id == owner_id),
                key=lambda event: (event.created_at, str(event.id)),
                reverse=True,
            )
