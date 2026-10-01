"""Thread-safe in-memory identity adapter for local development and isolated tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import RLock
from uuid import UUID

from apistra.modules.identity.domain import Administrator, AuditEvent, Session, SessionContext


class InMemoryIdentityStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._administrator: Administrator | None = None
        self._sessions: dict[str, Session] = {}
        self.audit_events: list[AuditEvent] = []

    def bootstrap(
        self,
        administrator: Administrator,
        session: Session,
        audit_event: AuditEvent,
    ) -> bool:
        with self._lock:
            if self._administrator is not None:
                return False
            self._administrator = administrator
            self._sessions[session.token_hash] = session
            self.audit_events.append(audit_event)
            return True

    def installation_has_administrator(self) -> bool:
        with self._lock:
            return self._administrator is not None

    def find_administrator(self, username: str) -> Administrator | None:
        with self._lock:
            if self._administrator and self._administrator.username == username:
                return self._administrator
            return None

    def create_session(self, session: Session, audit_event: AuditEvent) -> None:
        with self._lock:
            self._sessions[session.token_hash] = session
            self.audit_events.append(audit_event)

    def find_session(self, token_hash: str) -> SessionContext | None:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None or self._administrator is None:
                return None
            return SessionContext(session, self._administrator.username)

    def revoke_session(
        self,
        token_hash: str,
        csrf_hash: str,
        revoked_at: datetime,
        audit_event: AuditEvent,
    ) -> bool:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None or session.revoked_at is not None or session.csrf_hash != csrf_hash:
                return False
            self._sessions[token_hash] = replace(session, revoked_at=revoked_at)
            self.audit_events.append(audit_event)
            return True

    def list_audit_events(self, actor_id: UUID) -> list[AuditEvent]:
        with self._lock:
            return sorted(
                (event for event in self.audit_events if event.actor_id == actor_id),
                key=lambda event: (event.created_at, str(event.id)),
                reverse=True,
            )
