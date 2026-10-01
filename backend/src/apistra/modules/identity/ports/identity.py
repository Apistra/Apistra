"""Ports owned by the identity module."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.identity.domain import Administrator, AuditEvent, Session, SessionContext


class Clock(Protocol):
    def now(self) -> datetime: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...


class TokenService(Protocol):
    def issue(self) -> tuple[str, str]: ...

    def digest(self, raw_token: str) -> str: ...


class IdentityStore(Protocol):
    def bootstrap(
        self,
        administrator: Administrator,
        session: Session,
        audit_event: AuditEvent,
    ) -> bool: ...

    def installation_has_administrator(self) -> bool: ...

    def find_administrator(self, username: str) -> Administrator | None: ...

    def create_session(self, session: Session, audit_event: AuditEvent) -> None: ...

    def find_session(self, token_hash: str) -> SessionContext | None: ...

    def revoke_session(
        self,
        token_hash: str,
        csrf_hash: str,
        revoked_at: datetime,
        audit_event: AuditEvent,
    ) -> bool: ...

    def list_audit_events(self, actor_id: UUID) -> list[AuditEvent]: ...
