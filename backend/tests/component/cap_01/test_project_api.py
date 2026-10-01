from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.platform.runtime import RuntimeSettings


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 1, 14, tzinfo=UTC)


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


def client() -> tuple[TestClient, ProjectService, InMemoryProjectStore, str]:
    identity_store = InMemoryIdentityStore()
    identity = IdentityService(identity_store, Hasher(), Tokens(), Clock(), timedelta(hours=12))
    project_store = InMemoryProjectStore()
    projects = ProjectService(project_store, Clock())
    runtime = RuntimeSettings("api", "0.1.0", "commit", "test", secure_cookies=True)
    api = TestClient(create_app(runtime, identity, projects), base_url="https://testserver")
    receipt = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "admin.alpha", "password": "correct horse battery"},
    ).json()
    return api, projects, project_store, receipt["csrf_token"]


def mutation_headers(csrf: str, **extra: str) -> dict[str, str]:
    return {"x-csrf-token": csrf, **extra}


def test_project_http_lifecycle_is_authenticated_versioned_and_idempotent() -> None:
    api, _projects, store, csrf = client()
    payload = {"name": "Atlas Research", "key": "atlas"}
    headers = mutation_headers(csrf, **{"idempotency-key": "create-atlas"})
    created = api.post("/api/v1/projects", json=payload, headers=headers)
    replay = api.post("/api/v1/projects", json=payload, headers=headers)
    assert created.status_code == replay.status_code == 201
    assert created.json()["id"] == replay.json()["id"]
    assert created.json()["key"] == "ATLAS"
    assert created.headers["etag"] == '"1"'
    assert len(store.audit_events) == 1

    project_id = created.json()["id"]
    listed = api.get("/api/v1/projects")
    assert [item["id"] for item in listed.json()["items"]] == [project_id]
    read = api.get(f"/api/v1/projects/{project_id}")
    assert read.headers["etag"] == '"1"'

    updated = api.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Atlas Platform", "key": "ATLAS-2"},
        headers=mutation_headers(csrf, **{"if-match": '"1"'}),
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    stale = api.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Stale", "key": "STALE"},
        headers=mutation_headers(csrf, **{"if-match": '"1"'}),
    )
    assert stale.status_code == 409
    assert stale.json()["title"] == "project.version_conflict"
    archived = api.post(
        f"/api/v1/projects/{project_id}:archive",
        headers=mutation_headers(csrf, **{"if-match": '"2"'}),
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"


def test_anonymous_csrf_foreign_and_unknown_requests_disclose_nothing() -> None:
    api, projects, _store, csrf = client()
    own = api.post(
        "/api/v1/projects",
        json={"name": "Atlas Research", "key": "ATLAS"},
        headers=mutation_headers(csrf, **{"idempotency-key": "own"}),
    ).json()
    assert api.get("/api/v1/projects", headers={"cookie": ""}).status_code == 401
    rejected_csrf = api.patch(
        f"/api/v1/projects/{own['id']}",
        json={"name": "Changed", "key": "CHANGED"},
        headers={"if-match": '"1"', "x-csrf-token": "wrong"},
    )
    assert rejected_csrf.status_code == 403

    foreign = projects.create(
        uuid4(), "other.admin", "Foreign Secret", "SECRET", "foreign", "corr"
    ).value
    foreign_response = api.get(f"/api/v1/projects/{foreign.id}")
    unknown_response = api.get(f"/api/v1/projects/{uuid4()}")
    assert foreign_response.status_code == unknown_response.status_code == 404
    foreign_problem = foreign_response.json()
    unknown_problem = unknown_response.json()
    foreign_problem.pop("correlation_id")
    unknown_problem.pop("correlation_id")
    assert foreign_problem == unknown_problem
    assert "Foreign Secret" not in foreign_response.text
    assert "SECRET" not in foreign_response.text


def test_project_request_contract_rejects_missing_headers_and_extra_fields() -> None:
    api, _projects, _store, csrf = client()
    no_idempotency = api.post(
        "/api/v1/projects",
        json={"name": "Atlas", "key": "ATLAS"},
        headers=mutation_headers(csrf),
    )
    extra = api.post(
        "/api/v1/projects",
        json={"name": "Atlas", "key": "ATLAS", "owner": "someone"},
        headers=mutation_headers(csrf, **{"idempotency-key": "extra"}),
    )
    assert no_idempotency.status_code == 422
    assert extra.status_code == 422


def test_audit_api_is_authenticated_attributable_and_owner_scoped() -> None:
    api, projects, _store, csrf = client()
    owned = api.post(
        "/api/v1/projects",
        json={"name": "Atlas Research", "key": "ATLAS"},
        headers=mutation_headers(
            csrf,
            **{
                "idempotency-key": "own-audit",
                "x-correlation-id": "corr-owned-project",
            },
        ),
    ).json()
    foreign = projects.create(
        uuid4(), "foreign.admin", "Foreign Secret", "SECRET", "foreign-audit", "corr-foreign"
    ).value

    response = api.get("/api/v1/audit-events")

    assert response.status_code == 200
    events = response.json()["items"]
    assert {event["event_type"] for event in events} >= {
        "administrator.bootstrap.completed",
        "project.created",
    }
    project_event = next(event for event in events if event["event_type"] == "project.created")
    assert project_event["project_id"] == owned["id"]
    assert project_event["project_key"] == "ATLAS"
    assert project_event["actor"] == "admin.alpha"
    assert project_event["correlation_id"] == "corr-owned-project"
    assert str(foreign.id) not in response.text
    assert "Foreign Secret" not in response.text
    assert "SECRET" not in response.text
    assert "corr-foreign" not in response.text
    assert api.get("/api/v1/audit-events", headers={"cookie": ""}).status_code == 401


def test_revocation_is_visible_only_after_a_new_authenticated_session() -> None:
    api, _projects, _store, csrf = client()
    assert (
        api.delete(
            "/api/v1/session",
            headers={"x-csrf-token": csrf},
        ).status_code
        == 204
    )
    assert api.get("/api/v1/audit-events").status_code == 401

    signed_in = api.post(
        "/api/v1/sessions",
        json={"username": "admin.alpha", "password": "correct horse battery"},
    )
    assert signed_in.status_code == 201
    events = api.get("/api/v1/audit-events").json()["items"]
    assert "session.revoked" in {event["event_type"] for event in events}
