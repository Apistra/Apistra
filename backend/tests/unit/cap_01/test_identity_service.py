from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.domain import IdentityErrorCode


class FixedClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 10, 1, 12, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == self.hash(password)


class FakeTokens:
    def __init__(self) -> None:
        self._counter = 0

    def issue(self) -> tuple[str, str]:
        self._counter += 1
        raw = f"token-{self._counter}"
        return raw, self.digest(raw)

    def digest(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()


def service() -> tuple[IdentityService, InMemoryIdentityStore, FixedClock]:
    store = InMemoryIdentityStore()
    clock = FixedClock()
    return (
        IdentityService(store, FakeHasher(), FakeTokens(), clock, timedelta(hours=12)),
        store,
        clock,
    )


def test_bootstrap_is_single_use_and_audited_without_secrets() -> None:
    identity, store, _clock = service()
    first = identity.bootstrap("administrator", "correct horse battery", "corr-1")
    replay = identity.bootstrap("another-admin", "another valid password", "corr-2")

    assert first.succeeded
    assert replay.error and replay.error.code is IdentityErrorCode.BOOTSTRAP_CLOSED
    assert identity.installation_status() == {"bootstrap_available": False}
    assert [event.event_type for event in store.audit_events] == [
        "identity.administrator.bootstrapped"
    ]
    assert "correct horse battery" not in repr(store.audit_events)
    assert first.value.raw_token not in repr(store.audit_events)


def test_concurrent_bootstrap_creates_exactly_one_administrator() -> None:
    identity, store, _clock = service()

    def attempt(index: int) -> bool:
        result = identity.bootstrap(
            f"administrator-{index}",
            "correct horse battery",
            f"corr-{index}",
        )
        return result.succeeded

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attempt, range(8)))

    assert results.count(True) == 1
    assert len(store.audit_events) == 1


def test_authentication_is_non_disclosing_and_creates_rotated_session() -> None:
    identity, _store, _clock = service()
    bootstrap = identity.bootstrap("administrator", "correct horse battery", "corr-1")
    signed_in = identity.authenticate("administrator", "correct horse battery", "corr-2")
    wrong_password = identity.authenticate("administrator", "wrong password", "corr-3")
    unknown_user = identity.authenticate("somebody-else", "wrong password", "corr-4")

    assert signed_in.succeeded
    assert signed_in.value.raw_token != bootstrap.value.raw_token
    assert wrong_password.error == unknown_user.error
    assert wrong_password.error.code is IdentityErrorCode.INVALID_CREDENTIALS


def test_session_requires_matching_csrf_and_revocation_is_immediate() -> None:
    identity, store, _clock = service()
    issued = identity.bootstrap("administrator", "correct horse battery", "corr-1").value

    rejected = identity.revoke_session(issued.raw_token, "wrong", "corr-2")
    assert rejected.error and rejected.error.code is IdentityErrorCode.CSRF_INVALID
    assert identity.verify_session(issued.raw_token).succeeded

    revoked = identity.revoke_session(issued.raw_token, issued.csrf_token, "corr-3")
    assert revoked.succeeded
    assert identity.verify_session(issued.raw_token).error.code is IdentityErrorCode.SESSION_INVALID
    assert [event.event_type for event in store.audit_events][-1] == "identity.session.revoked"


def test_expired_and_missing_sessions_are_rejected_identically() -> None:
    identity, _store, clock = service()
    issued = identity.bootstrap("administrator", "correct horse battery", "corr-1").value
    clock.value += timedelta(hours=12)

    expired = identity.verify_session(issued.raw_token)
    missing = identity.verify_session(None)
    assert expired.error == missing.error


def test_credential_boundaries_fail_closed() -> None:
    identity, _store, _clock = service()
    too_short = identity.bootstrap("ad", "correct horse battery", "corr-1")
    weak = identity.bootstrap("administrator", "short", "corr-2")
    excessive = identity.bootstrap("administrator", "x" * 1025, "corr-3")
    assert {too_short.error.code, weak.error.code, excessive.error.code} == {
        IdentityErrorCode.INVALID_INPUT
    }


def test_session_ttl_is_bounded() -> None:
    store = InMemoryIdentityStore()
    for invalid in (timedelta(minutes=4), timedelta(hours=25)):
        try:
            IdentityService(store, FakeHasher(), FakeTokens(), FixedClock(), invalid)
        except ValueError as error:
            assert "session_ttl" in str(error)
        else:
            raise AssertionError("invalid session TTL was accepted")
