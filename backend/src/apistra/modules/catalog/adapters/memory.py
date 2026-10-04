"""Thread-safe in-memory secret store for local development and tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import RLock
from uuid import UUID

from apistra.modules.catalog.domain import (
    EncryptedSecretEnvelope,
    SecretAuditEvent,
    SecretReference,
    SecretStatus,
)


class InMemorySecretStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._references: dict[UUID, SecretReference] = {}
        self._idempotency: dict[tuple[UUID, UUID, str], tuple[str, UUID]] = {}
        self.audit_events: list[SecretAuditEvent] = []

    def create(
        self,
        reference: SecretReference,
        event: SecretAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[SecretReference | None, str | None]:
        with self._lock:
            identity = (
                reference.owner_administrator_id,
                reference.project_id,
                idempotency_key,
            )
            replay = self._idempotency.get(identity)
            if replay:
                fingerprint, reference_id = replay
                if fingerprint != request_fingerprint:
                    return None, "idempotency"
                return self._references[reference_id], None
            if any(
                item.owner_administrator_id == reference.owner_administrator_id
                and item.project_id == reference.project_id
                and item.name == reference.name
                and item.status is SecretStatus.ACTIVE
                for item in self._references.values()
            ):
                return None, "name"
            self._references[reference.id] = reference
            self._idempotency[identity] = (request_fingerprint, reference.id)
            self.audit_events.append(event)
            return reference, None

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[SecretReference]:
        with self._lock:
            return sorted(
                (
                    item
                    for item in self._references.values()
                    if item.owner_administrator_id == owner_id and item.project_id == project_id
                ),
                key=lambda item: (item.name, str(item.id)),
            )

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> SecretReference | None:
        with self._lock:
            reference = self._references.get(reference_id)
            if (
                reference
                and reference.owner_administrator_id == owner_id
                and reference.project_id == project_id
            ):
                return reference
            return None

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
        with self._lock:
            current = self.get_for_project(owner_id, project_id, reference_id)
            if current is None:
                return None, "not_found"
            if current.version != expected_version or current.status is SecretStatus.REVOKED:
                return None, "version"
            updated = replace(
                current,
                envelope=envelope,
                version=current.version + 1,
                updated_at=updated_at,
            )
            self._references[reference_id] = updated
            self.audit_events.append(replace(event, created_at=updated_at))
            return updated, None

    def revoke(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: SecretAuditEvent,
    ) -> tuple[SecretReference | None, str | None]:
        with self._lock:
            current = self.get_for_project(owner_id, project_id, reference_id)
            if current is None:
                return None, "not_found"
            if current.version != expected_version or current.status is SecretStatus.REVOKED:
                return None, "version"
            revoked = replace(
                current,
                status=SecretStatus.REVOKED,
                version=current.version + 1,
                updated_at=updated_at,
            )
            self._references[reference_id] = revoked
            self.audit_events.append(replace(event, created_at=updated_at))
            return revoked, None

    def list_audit_for_owner(self, owner_id: UUID) -> list[SecretAuditEvent]:
        with self._lock:
            return sorted(
                (event for event in self.audit_events if event.actor_id == owner_id),
                key=lambda event: (event.created_at, str(event.id)),
                reverse=True,
            )
