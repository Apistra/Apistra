"""Provider-neutral ports owned by the catalogue module."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.catalog.domain import (
    EncryptedSecretEnvelope,
    SecretAuditEvent,
    SecretReference,
)


class SecretClock(Protocol):
    def now(self) -> datetime: ...


class SecretCipher(Protocol):
    def encrypt(self, plaintext: bytes, associated_data: bytes) -> EncryptedSecretEnvelope: ...

    def decrypt(self, envelope: EncryptedSecretEnvelope, associated_data: bytes) -> bytes: ...


class SecretStore(Protocol):
    def create(
        self,
        reference: SecretReference,
        event: SecretAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[SecretReference | None, str | None]: ...

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[SecretReference]: ...

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> SecretReference | None: ...

    def replace(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        envelope: EncryptedSecretEnvelope,
        updated_at: datetime,
        event: SecretAuditEvent,
    ) -> tuple[SecretReference | None, str | None]: ...

    def revoke(
        self,
        owner_id: UUID,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        updated_at: datetime,
        event: SecretAuditEvent,
    ) -> tuple[SecretReference | None, str | None]: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[SecretAuditEvent]: ...
