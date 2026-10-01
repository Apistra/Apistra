"""Domain values for the local identity boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class IdentityErrorCode(StrEnum):
    """Stable, non-disclosing error taxonomy exposed by the application boundary."""

    BOOTSTRAP_CLOSED = "identity.bootstrap_closed"
    INVALID_INPUT = "identity.invalid_input"
    INVALID_CREDENTIALS = "identity.invalid_credentials"
    SESSION_INVALID = "identity.session_invalid"
    CSRF_INVALID = "identity.csrf_invalid"


@dataclass(frozen=True, slots=True)
class IdentityError:
    code: IdentityErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class Administrator:
    id: UUID
    username: str
    password_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Session:
    id: UUID
    administrator_id: UUID
    token_hash: str
    csrf_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and now < self.expires_at


@dataclass(frozen=True, slots=True)
class SessionContext:
    session: Session
    administrator_username: str


@dataclass(frozen=True, slots=True)
class IssuedSession:
    administrator_id: UUID
    administrator_username: str
    raw_token: str
    csrf_token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID | None = None
    actor_username: str | None = None
    subject_id: UUID | None = None
    details: dict[str, Any] = field(default_factory=dict)
