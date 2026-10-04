from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.platform.runtime import RuntimeSettings

CANARY = "CAP02-CANARY-never-visible"


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 4, 12, tzinfo=UTC)


class Hasher:
    def hash(self, password: str) -> str:
        return f"hash:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == self.hash(password)


class Tokens:
    def issue(self) -> tuple[str, str]:
        return "opaque-session", self.digest("opaque-session")

    def digest(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()


def client() -> tuple[TestClient, str, str, InMemorySecretStore]:
    identity = IdentityService(
        InMemoryIdentityStore(), Hasher(), Tokens(), Clock(), timedelta(hours=12)
    )
    projects = ProjectService(InMemoryProjectStore(), Clock())
    secret_store = InMemorySecretStore()
    secrets = SecretService(
        secret_store,
        AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))}),
        Clock(),
        "installation-test",
    )
    api = TestClient(
        create_app(
            RuntimeSettings("api", "0.2.0", "commit", "test"),
            identity,
            projects,
            secrets,
        ),
        base_url="https://testserver",
    )
    session = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "admin.alpha", "password": "correct horse battery"},
    ).json()
    project = api.post(
        "/api/v1/projects",
        json={"name": "Atlas Research", "key": "ATLAS"},
        headers={
            "x-csrf-token": session["csrf_token"],
            "idempotency-key": "create-atlas",
        },
    ).json()
    return api, session["csrf_token"], project["id"], secret_store


def test_http_secret_lifecycle_is_write_only_project_scoped_and_audited() -> None:
    api, csrf, project_id, store = client()
    headers = {"x-csrf-token": csrf, "idempotency-key": "create-secret"}
    created = api.post(
        f"/api/v1/projects/{project_id}/secrets",
        json={"name": "provider-primary", "purpose": "Primary endpoint", "value": CANARY},
        headers=headers,
    )
    replay = api.post(
        f"/api/v1/projects/{project_id}/secrets",
        json={"name": "provider-primary", "purpose": "Primary endpoint", "value": CANARY},
        headers=headers,
    )
    assert created.status_code == replay.status_code == 201
    assert created.json()["id"] == replay.json()["id"]
    assert CANARY not in created.text
    assert "ciphertext" not in created.text and "key_id" not in created.text
    assert created.headers["etag"] == '"1"'

    listed = api.get(f"/api/v1/projects/{project_id}/secrets")
    assert listed.status_code == 200 and CANARY not in listed.text
    replaced = api.put(
        f"/api/v1/projects/{project_id}/secrets/{created.json()['id']}",
        json={"value": "rotated-value"},
        headers={"x-csrf-token": csrf, "if-match": '"1"'},
    )
    assert replaced.json()["version"] == 2 and "rotated-value" not in replaced.text
    audit = api.get("/api/v1/audit-events")
    assert "secret.created" in audit.text and "secret.replaced" in audit.text
    assert CANARY not in audit.text and "rotated-value" not in audit.text
    revoked = api.delete(
        f"/api/v1/projects/{project_id}/secrets/{created.json()['id']}",
        headers={"x-csrf-token": csrf, "if-match": '"2"'},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "REVOKED"
    denied_replay = api.delete(
        f"/api/v1/projects/{project_id}/secrets/{created.json()['id']}",
        headers={"x-csrf-token": csrf, "if-match": '"3"'},
    )
    assert denied_replay.status_code == 404
    assert denied_replay.json()["detail"] == "Secret reference is unavailable."
    assert len(store.audit_events) == 3


def test_anonymous_foreign_unknown_and_stale_requests_fail_safely() -> None:
    api, csrf, project_id, _store = client()
    created = api.post(
        f"/api/v1/projects/{project_id}/secrets",
        json={"name": "provider-primary", "purpose": "Primary endpoint", "value": CANARY},
        headers={"x-csrf-token": csrf, "idempotency-key": "create-secret"},
    ).json()
    assert (
        api.get(f"/api/v1/projects/{project_id}/secrets", headers={"cookie": ""}).status_code == 401
    )
    unknown = api.put(
        f"/api/v1/projects/{project_id}/secrets/00000000-0000-0000-0000-000000000000",
        json={"value": "replacement"},
        headers={"x-csrf-token": csrf, "if-match": '"1"'},
    )
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Secret reference is unavailable."
    stale = api.put(
        f"/api/v1/projects/{project_id}/secrets/{created['id']}",
        json={"value": "replacement"},
        headers={"x-csrf-token": csrf, "if-match": '"9"'},
    )
    assert stale.status_code == 409 and stale.json()["title"] == "secret.version_conflict"
    assert CANARY not in unknown.text + stale.text
