"""Use cases for local administrator bootstrap and revocable sessions."""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

from apistra.modules.identity.domain import (
    Administrator,
    AuditEvent,
    IdentityError,
    IdentityErrorCode,
    IssuedSession,
    Session,
    SessionContext,
)
from apistra.modules.identity.ports import Clock, IdentityStore, PasswordHasher, TokenService

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,127}$")
MINIMUM_PASSWORD_LENGTH = 12
MAXIMUM_PASSWORD_LENGTH = 1024


@dataclass(frozen=True, slots=True)
class OperationResult[T]:
    value: T | None = None
    error: IdentityError | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class IdentityService:
    """Coordinates identity use cases without depending on transport or persistence."""

    def __init__(
        self,
        store: IdentityStore,
        password_hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
        session_ttl: timedelta,
    ) -> None:
        if not timedelta(minutes=5) <= session_ttl <= timedelta(hours=24):
            raise ValueError("session_ttl must be between 5 minutes and 24 hours")
        self._store = store
        self._password_hasher = password_hasher
        self._tokens = tokens
        self._clock = clock
        self._session_ttl = session_ttl
        self._dummy_password_hash = password_hasher.hash("not-a-real-credential")

    def installation_status(self) -> dict[str, bool]:
        return {"bootstrap_available": not self._store.installation_has_administrator()}

    def bootstrap(
        self,
        username: str,
        password: str,
        correlation_id: str,
    ) -> OperationResult[IssuedSession]:
        validation_error = self._validate_credentials(username, password)
        if validation_error:
            return OperationResult(error=validation_error)
        now = self._clock.now()
        administrator = Administrator(uuid4(), username, self._password_hasher.hash(password), now)
        issued, session = self._new_session(administrator, now)
        event = AuditEvent(
            id=uuid4(),
            event_type="administrator.bootstrap.completed",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=administrator.id,
            actor_username=administrator.username,
            subject_id=administrator.id,
            details={"installation_id": "local"},
        )
        if not self._store.bootstrap(administrator, session, event):
            return OperationResult(
                error=IdentityError(
                    IdentityErrorCode.BOOTSTRAP_CLOSED,
                    "Administrator bootstrap is not available.",
                )
            )
        return OperationResult(value=issued)

    def authenticate(
        self,
        username: str,
        password: str,
        correlation_id: str,
    ) -> OperationResult[IssuedSession]:
        administrator = self._store.find_administrator(username)
        password_hash = administrator.password_hash if administrator else self._dummy_password_hash
        valid = self._password_hasher.verify(password_hash, password)
        if administrator is None or not valid:
            return OperationResult(
                error=IdentityError(
                    IdentityErrorCode.INVALID_CREDENTIALS,
                    "The username or password is invalid.",
                )
            )
        now = self._clock.now()
        issued, session = self._new_session(administrator, now)
        event = AuditEvent(
            id=uuid4(),
            event_type="session.created",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=administrator.id,
            actor_username=administrator.username,
            subject_id=session.id,
        )
        self._store.create_session(session, event)
        return OperationResult(value=issued)

    def verify_session(self, raw_token: str | None) -> OperationResult[SessionContext]:
        if not raw_token:
            return self._invalid_session()
        context = self._store.find_session(self._tokens.digest(raw_token))
        if context is None or not context.session.is_active(self._clock.now()):
            return self._invalid_session()
        return OperationResult(value=context)

    def authorize_mutation(
        self, raw_token: str | None, csrf_token: str | None
    ) -> OperationResult[SessionContext]:
        """Verify a session and its double-submit CSRF value without changing state."""

        result = self.verify_session(raw_token)
        if result.error:
            return result
        context = result.value
        supplied_csrf_hash = self._tokens.digest(csrf_token or "")
        if not csrf_token or not hmac.compare_digest(context.session.csrf_hash, supplied_csrf_hash):
            return OperationResult(
                error=IdentityError(
                    IdentityErrorCode.CSRF_INVALID,
                    "The request could not be verified.",
                )
            )
        return result

    def audit_events(self, administrator_id: UUID) -> list[AuditEvent]:
        """Return only audit records attributable to the authenticated Administrator."""

        return self._store.list_audit_events(administrator_id)

    def revoke_session(
        self,
        raw_token: str | None,
        csrf_token: str | None,
        correlation_id: str,
    ) -> OperationResult[None]:
        if not raw_token:
            return self._invalid_session()
        context = self._store.find_session(self._tokens.digest(raw_token))
        if context is None or not context.session.is_active(self._clock.now()):
            return self._invalid_session()
        supplied_csrf_hash = self._tokens.digest(csrf_token or "")
        if not csrf_token or not hmac.compare_digest(context.session.csrf_hash, supplied_csrf_hash):
            return OperationResult(
                error=IdentityError(
                    IdentityErrorCode.CSRF_INVALID, "The request could not be verified."
                )
            )
        now = self._clock.now()
        event = AuditEvent(
            id=uuid4(),
            event_type="session.revoked",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=context.session.administrator_id,
            actor_username=context.administrator_username,
            subject_id=context.session.id,
        )
        if not self._store.revoke_session(
            context.session.token_hash,
            supplied_csrf_hash,
            now,
            event,
        ):
            return self._invalid_session()
        return OperationResult()

    def _new_session(self, administrator: Administrator, now) -> tuple[IssuedSession, Session]:
        raw_token, token_hash = self._tokens.issue()
        csrf_token, csrf_hash = self._tokens.issue()
        expires_at = now + self._session_ttl
        session = Session(
            id=uuid4(),
            administrator_id=administrator.id,
            token_hash=token_hash,
            csrf_hash=csrf_hash,
            created_at=now,
            expires_at=expires_at,
        )
        issued = IssuedSession(
            administrator_id=administrator.id,
            administrator_username=administrator.username,
            raw_token=raw_token,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )
        return issued, session

    @staticmethod
    def _validate_credentials(username: str, password: str) -> IdentityError | None:
        if not USERNAME_PATTERN.fullmatch(username):
            return IdentityError(
                IdentityErrorCode.INVALID_INPUT,
                "Username must contain 3 to 128 approved characters.",
            )
        if not MINIMUM_PASSWORD_LENGTH <= len(password) <= MAXIMUM_PASSWORD_LENGTH:
            return IdentityError(
                IdentityErrorCode.INVALID_INPUT,
                "Password must contain 12 to 1024 characters.",
            )
        return None

    @staticmethod
    def _invalid_session() -> OperationResult:
        return OperationResult(
            error=IdentityError(
                IdentityErrorCode.SESSION_INVALID,
                "The session is invalid or expired. Sign in again.",
            )
        )
