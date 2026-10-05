"""Project-scoped HTTP policy boundary and exact budget decisions."""

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.platform.runtime import RuntimeSettings


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 5, 10, tzinfo=UTC)


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


def client() -> tuple[TestClient, str, str]:
    identity = IdentityService(
        InMemoryIdentityStore(), Hasher(), Tokens(), Clock(), timedelta(hours=12)
    )
    projects = ProjectService(InMemoryProjectStore(), Clock())
    api = TestClient(
        create_app(RuntimeSettings("api", "0.2.0", "commit", "test"), identity, projects),
        base_url="https://testserver",
    )
    session = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "admin.alpha", "password": "correct horse battery"},
    ).json()
    project = api.post(
        "/api/v1/projects",
        json={"name": "Atlas Research", "key": "ATLAS"},
        headers={"x-csrf-token": session["csrf_token"], "idempotency-key": "atlas"},
    ).json()
    return api, session["csrf_token"], project["id"]


def policy_payload() -> dict[str, object]:
    return {
        "name": "interactive-default",
        "maximum_duration_seconds": 300,
        "maximum_calls": 10,
        "maximum_tokens": 20_000,
        "maximum_cost_minor_units": 150,
        "currency": "EUR",
        "maximum_concurrency": 2,
        "rate_limit_requests": 30,
        "rate_limit_window_seconds": 60,
        "warning_threshold_percent": None,
    }


def observation(**changed: int) -> dict[str, int]:
    values = {
        "duration_seconds": 0,
        "calls": 0,
        "tokens": 0,
        "cost_minor_units": 0,
        "concurrency": 0,
        "requests_in_window": 0,
        "rate_window_seconds": 60,
    }
    values.update(changed)
    return values


def test_create_replay_version_conflict_and_exact_boundary() -> None:
    api, csrf, project = client()
    route = f"/api/v1/projects/{project}/policies/limits"
    headers = {"x-csrf-token": csrf, "idempotency-key": "policy-v1"}
    created = api.post(route, json=policy_payload(), headers=headers)
    replay = api.post(route, json=policy_payload(), headers=headers)
    assert created.status_code == replay.status_code == 201
    assert created.json() == replay.json()
    assert created.headers["etag"] == '"1"'
    policy_id = created.json()["policy_id"]
    assert api.get(route).json()["items"][0]["policy_id"] == policy_id
    evaluation_route = f"{route}/{policy_id}/versions/1:evaluate"
    for calls, expected in [(9, "ALLOW"), (10, "ALLOW"), (11, "DENY")]:
        response = api.post(
            evaluation_route,
            json=observation(calls=calls),
            headers={"x-csrf-token": csrf},
        )
        assert response.status_code == 200
        assert response.json()["decision"] == expected
        assert response.json()["effect_permitted"] == (calls <= 10)
    assert "policy.limit_evaluated" in api.get("/api/v1/audit-events").text
    unknown_version = api.post(
        f"{route}/{policy_id}/versions/99:evaluate",
        json=observation(),
        headers={"x-csrf-token": csrf},
    )
    assert unknown_version.status_code == 404
    versions_route = f"{route}/{policy_id}/versions"
    missing_match = api.post(
        versions_route,
        json={**policy_payload(), "maximum_calls": 12},
        headers={"x-csrf-token": csrf, "idempotency-key": "policy-v2"},
    )
    assert missing_match.status_code == 422
    draft = api.post(
        versions_route,
        json={**policy_payload(), "maximum_calls": 12},
        headers={"x-csrf-token": csrf, "idempotency-key": "policy-v2", "if-match": '"1"'},
    )
    assert draft.status_code == 201
    assert draft.json()["status"] == "DRAFT"
    assert (
        api.post(
            f"{route}/{policy_id}/versions/2:evaluate",
            json=observation(),
            headers={"x-csrf-token": csrf},
        ).status_code
        == 404
    )
    published = api.post(
        f"{route}/{policy_id}/versions/2:publish",
        headers={"x-csrf-token": csrf},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    stale = api.post(
        versions_route,
        json={**policy_payload(), "maximum_calls": 13},
        headers={"x-csrf-token": csrf, "idempotency-key": "policy-v3", "if-match": '"1"'},
    )
    assert stale.status_code == 409
    assert "This draft changed elsewhere" in stale.json()["detail"]
    assert [item["version"] for item in api.get(versions_route).json()["items"]] == [2, 1]


def test_foreign_project_and_anonymous_or_csrf_missing_are_denied() -> None:
    api, csrf, project = client()
    route = f"/api/v1/projects/{project}/policies/limits"
    assert api.get(route, headers={"cookie": ""}).status_code == 401
    assert api.post(route, json=policy_payload()).status_code == 403
    created = api.post(
        route,
        json=policy_payload(),
        headers={"x-csrf-token": csrf, "idempotency-key": "policy-v1"},
    ).json()
    other = api.post(
        "/api/v1/projects",
        json={"name": "Orion Research", "key": "ORION"},
        headers={"x-csrf-token": csrf, "idempotency-key": "orion"},
    ).json()["id"]
    foreign = api.post(
        f"/api/v1/projects/{other}/policies/limits/{created['policy_id']}/versions/1:evaluate",
        json=observation(),
        headers={"x-csrf-token": csrf},
    )
    assert foreign.status_code == 404
    assert created["name"] not in foreign.text
    revoked = api.delete("/api/v1/session", headers={"x-csrf-token": csrf})
    assert revoked.status_code == 204
    assert api.get(route).status_code == 401
