"""Domain types for write-only project secret references."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class SecretStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class SecretErrorCode(StrEnum):
    INVALID_INPUT = "secret.invalid_input"
    UNAVAILABLE = "secret.unavailable"
    NAME_CONFLICT = "secret.name_conflict"
    VERSION_CONFLICT = "secret.version_conflict"
    IDEMPOTENCY_CONFLICT = "secret.idempotency_conflict"


@dataclass(frozen=True, slots=True)
class SecretError:
    code: SecretErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class EncryptedSecretEnvelope:
    format_version: int
    key_id: str
    nonce: bytes
    ciphertext: bytes


@dataclass(frozen=True, slots=True)
class SecretReference:
    id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    name: str
    purpose: str
    status: SecretStatus
    version: int
    envelope: EncryptedSecretEnvelope
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SecretAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    secret_reference_id: UUID
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, repr=False)
class SecretMaterial:
    """Short-lived plaintext returned only to an authorised internal adapter."""

    value: bytes

    def __repr__(self) -> str:
        return "SecretMaterial(<redacted>)"
