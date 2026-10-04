"""Secret-reference use cases and disclosure-safe failure mapping."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from apistra.modules.catalog.domain import (
    SecretAuditEvent,
    SecretError,
    SecretErrorCode,
    SecretMaterial,
    SecretReference,
    SecretStatus,
)
from apistra.modules.catalog.ports import SecretCipher, SecretClock, SecretStore

SECRET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
MAXIMUM_PURPOSE_LENGTH = 256
MAXIMUM_SECRET_BYTES = 65_536
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
ENVELOPE_FORMAT_VERSION = 1
UNAVAILABLE_MESSAGE = "Secret reference is unavailable."
type SecretReferenceList = list[SecretReference]
type SecretAuditEventList = list[SecretAuditEvent]


@dataclass(frozen=True, slots=True)
class SecretResult[T]:
    value: T | None = None
    error: SecretError | None = None


class SecretService:
    def __init__(
        self,
        store: SecretStore,
        cipher: SecretCipher,
        clock: SecretClock,
        installation_id: str,
    ) -> None:
        self._store = store
        self._cipher = cipher
        self._clock = clock
        self._installation_id = installation_id

    def create(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        name: str,
        purpose: str,
        plaintext: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> SecretResult[SecretReference]:
        normalized_name = name.strip().lower()
        normalized_purpose = purpose.strip()
        validation = self._validate(normalized_name, normalized_purpose, plaintext)
        if validation:
            return SecretResult(error=validation)
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return self._invalid("Idempotency-Key must contain 1 to 128 characters.")
        now = self._clock.now()
        reference_id = uuid4()
        envelope = self._cipher.encrypt(
            plaintext.encode(),
            self._associated_data(project_id, reference_id, 1),
        )
        reference = SecretReference(
            id=reference_id,
            owner_administrator_id=owner_id,
            project_id=project_id,
            name=normalized_name,
            purpose=normalized_purpose,
            status=SecretStatus.ACTIVE,
            version=1,
            envelope=envelope,
            created_at=now,
            updated_at=now,
        )
        event = self._event("secret.created", reference, actor_username, correlation_id)
        fingerprint = hashlib.sha256(
            b"\0".join((normalized_name.encode(), normalized_purpose.encode(), plaintext.encode()))
        ).hexdigest()
        stored, conflict = self._store.create(reference, event, idempotency_key, fingerprint)
        return (
            SecretResult(value=stored)
            if stored
            else SecretResult(error=self._store_error(conflict))
        )

    def list(self, owner_id: UUID, project_id: UUID) -> SecretResult[SecretReferenceList]:
        return SecretResult(value=self._store.list_for_project(owner_id, project_id))

    def audit_events(self, owner_id: UUID) -> SecretResult[SecretAuditEventList]:
        return SecretResult(value=self._store.list_audit_for_owner(owner_id))

    def replace(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        plaintext: str,
        correlation_id: str,
    ) -> SecretResult[SecretReference]:
        current = self._store.get_for_project(owner_id, project_id, reference_id)
        if current is None or current.status is SecretStatus.REVOKED:
            return self._unavailable()
        if not plaintext or len(plaintext.encode()) > MAXIMUM_SECRET_BYTES:
            return self._invalid("Secret value is required and may contain at most 65536 bytes.")
        next_version = expected_version + 1
        envelope = self._cipher.encrypt(
            plaintext.encode(),
            self._associated_data(project_id, reference_id, next_version),
        )
        event = self._event(
            "secret.replaced",
            current,
            actor_username,
            correlation_id,
            {"from_version": expected_version, "to_version": next_version},
        )
        stored, conflict = self._store.replace(
            owner_id,
            project_id,
            reference_id,
            expected_version,
            envelope,
            self._clock.now(),
            event,
        )
        return (
            SecretResult(value=stored)
            if stored
            else SecretResult(error=self._store_error(conflict))
        )

    def revoke(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        reference_id: UUID,
        expected_version: int,
        correlation_id: str,
    ) -> SecretResult[SecretReference]:
        current = self._store.get_for_project(owner_id, project_id, reference_id)
        if current is None or current.status is SecretStatus.REVOKED:
            return self._unavailable()
        event = self._event(
            "secret.revoked",
            current,
            actor_username,
            correlation_id,
            {"from_version": expected_version},
        )
        stored, conflict = self._store.revoke(
            owner_id,
            project_id,
            reference_id,
            expected_version,
            self._clock.now(),
            event,
        )
        return (
            SecretResult(value=stored)
            if stored
            else SecretResult(error=self._store_error(conflict))
        )

    def resolve(
        self, owner_id: UUID, project_id: UUID, reference_id: UUID
    ) -> SecretResult[SecretMaterial]:
        reference = self._store.get_for_project(owner_id, project_id, reference_id)
        if reference is None or reference.status is SecretStatus.REVOKED:
            return self._unavailable()
        try:
            value = self._cipher.decrypt(
                reference.envelope,
                self._associated_data(project_id, reference_id, reference.version),
            )
        except ValueError:
            return self._unavailable()
        return SecretResult(value=SecretMaterial(value))

    def _associated_data(self, project_id: UUID, reference_id: UUID, version: int) -> bytes:
        return f"{self._installation_id}:{project_id}:{reference_id}:{version}".encode()

    @staticmethod
    def _validate(name: str, purpose: str, plaintext: str) -> SecretError | None:
        if not SECRET_NAME_PATTERN.fullmatch(name):
            return SecretError(
                SecretErrorCode.INVALID_INPUT,
                "Secret name must contain 2 to 64 lowercase letters, numbers, "
                "dots, dashes, or underscores.",
            )
        if not 1 <= len(purpose) <= MAXIMUM_PURPOSE_LENGTH:
            return SecretError(
                SecretErrorCode.INVALID_INPUT,
                "Purpose is required and may contain at most 256 characters.",
            )
        if not plaintext or len(plaintext.encode()) > MAXIMUM_SECRET_BYTES:
            return SecretError(
                SecretErrorCode.INVALID_INPUT,
                "Secret value is required and may contain at most 65536 bytes.",
            )
        return None

    @staticmethod
    def _event(
        event_type: str,
        reference: SecretReference,
        actor_username: str,
        correlation_id: str,
        details: dict[str, object] | None = None,
    ) -> SecretAuditEvent:
        return SecretAuditEvent(
            id=uuid4(),
            event_type=event_type,
            created_at=reference.updated_at,
            correlation_id=correlation_id,
            actor_id=reference.owner_administrator_id,
            actor_username=actor_username,
            project_id=reference.project_id,
            secret_reference_id=reference.id,
            details=details or {},
        )

    @staticmethod
    def _invalid(message: str) -> SecretResult[SecretReference]:
        return SecretResult(error=SecretError(SecretErrorCode.INVALID_INPUT, message))

    @staticmethod
    def _unavailable[T]() -> SecretResult[T]:
        return SecretResult(error=SecretError(SecretErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE))

    @staticmethod
    def _store_error(conflict: str | None) -> SecretError:
        if conflict == "name":
            return SecretError(SecretErrorCode.NAME_CONFLICT, "Secret name is already in use.")
        if conflict == "version":
            return SecretError(
                SecretErrorCode.VERSION_CONFLICT,
                "The secret reference has changed. Reload it and try again.",
            )
        if conflict == "idempotency":
            return SecretError(
                SecretErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        return SecretError(SecretErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE)
