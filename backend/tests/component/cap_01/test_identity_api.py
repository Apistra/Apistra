from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.platform.runtime import RuntimeSettings


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 1, 12, tzinfo=UTC)


class Hasher:
    def hash(self, password: str) -> str:
        return f"hash:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == self.hash(password)


class Tokens:
    def __init__(self) -> None:
        self.counter = 0

    def issue(self) -> tuple[str, str]:
        self.counter += 1
        raw = f"opaque-{self.counter}"
        return raw, self.digest(raw)

    def digest(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()


def client() -> tuple[TestClient, InMemoryIdentityStore]:
    store = InMemoryIdentityStore()
    identity = IdentityService(store, Hasher(), Tokens(), Clock(), timedelta(hours=12))
    runtime = RuntimeSettings("api", "0.1.0", "commit", "test", secure_cookies=True)
    return TestClient(create_app(runtime, identity), base_url="https://testserver"), store


def test_bootstrap_cookie_session_and_revocation_round_trip() -> None:
    api, store = client()
    assert api.get("/api/v1/installation").json() == {"bootstrap_available": True}

    created = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "administrator", "password": "correct horse battery"},
        headers={"x-correlation-id": "corr-bootstrap"},
    )
    assert created.status_code == 201
    assert "HttpOnly" in created.headers["set-cookie"]
    assert "Secure" in created.headers["set-cookie"]
    assert "SameSite=strict" in created.headers["set-cookie"]
    assert "opaque-1" not in created.text

    current = api.get("/api/v1/session")
    assert current.status_code == 200
    assert current.json()["administrator"]["username"] == "administrator"

    csrf = created.json()["csrf_token"]
    rejected = api.delete("/api/v1/session", headers={"x-csrf-token": "incorrect"})
    assert rejected.status_code == 403
    assert api.get("/api/v1/session").status_code == 200

    revoked = api.delete("/api/v1/session", headers={"x-csrf-token": csrf})
    assert revoked.status_code == 204
    assert api.get("/api/v1/session").status_code == 401
    assert [event.correlation_id for event in store.audit_events] == [
        "corr-bootstrap",
        revoked.headers["x-correlation-id"],
    ]


def test_bootstrap_replay_and_login_errors_do_not_disclose_identity() -> None:
    api, _store = client()
    payload = {"username": "administrator", "password": "correct horse battery"}
    assert api.post("/api/v1/administrators:bootstrap", json=payload).status_code == 201
    replay = api.post("/api/v1/administrators:bootstrap", json=payload)
    wrong = api.post(
        "/api/v1/sessions",
        json={"username": "administrator", "password": "wrong password!"},
    )
    unknown = api.post(
        "/api/v1/sessions",
        json={"username": "unknown-user", "password": "wrong password!"},
    )
    assert replay.status_code == 409
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]
    assert wrong.headers["content-type"].startswith("application/problem+json")


def test_request_schema_rejects_extra_and_oversized_input() -> None:
    api, _store = client()
    extra = api.post(
        "/api/v1/administrators:bootstrap",
        json={
            "username": "administrator",
            "password": "correct horse battery",
            "role": "superuser",
        },
    )
    oversized = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "administrator", "password": "x" * 1025},
    )
    assert extra.status_code == oversized.status_code == 422
