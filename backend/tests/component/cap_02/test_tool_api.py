from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.platform.runtime import RuntimeSettings

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
}


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 5, 9, tzinfo=UTC)


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
        create_app(
            RuntimeSettings("api", "0.2.0", "commit", "test"),
            identity,
            projects,
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
    return api, session["csrf_token"], project["id"]


def payload(effect_class: str = "WRITE") -> dict[str, object]:
    return {
        "name": "document-write",
        "description": "Replace a document.",
        "input_schema": SCHEMA,
        "output_schema": SCHEMA,
        "effect_class": effect_class,
        "actions": ["replace"],
    }


def test_tool_contract_is_project_scoped_versioned_idempotent_and_audited() -> None:
    api, csrf, project_id = client()
    headers = {"x-csrf-token": csrf, "idempotency-key": "tool-v1"}
    created = api.post(f"/api/v1/projects/{project_id}/tools", json=payload(), headers=headers)
    replay = api.post(f"/api/v1/projects/{project_id}/tools", json=payload(), headers=headers)
    assert created.status_code == replay.status_code == 201
    assert created.json() == replay.json()
    assert created.headers["etag"] == '"1"'
    assert created.json()["status"] == "PUBLISHED"

    tool_id = created.json()["tool_id"]
    draft = api.post(
        f"/api/v1/projects/{project_id}/tools/{tool_id}/versions",
        json={**payload(), "description": "Replace a document with approval."},
        headers={
            "x-csrf-token": csrf,
            "idempotency-key": "tool-v2",
            "if-match": '"1"',
        },
    )
    assert draft.status_code == 201
    assert draft.json()["status"] == "DRAFT"
    versions = api.get(f"/api/v1/projects/{project_id}/tools/{tool_id}/versions").json()["items"]
    assert [item["version"] for item in versions] == [2, 1]
    assert "tool.version_created" in api.get("/api/v1/audit-events").text


def test_tool_policy_defaults_fail_closed_and_rejects_undeclared_actions() -> None:
    api, csrf, project_id = client()
    created = api.post(
        f"/api/v1/projects/{project_id}/tools",
        json=payload(),
        headers={"x-csrf-token": csrf, "idempotency-key": "tool-v1"},
    ).json()
    route = f"/api/v1/projects/{project_id}/tools/{created['tool_id']}/versions/1:evaluate"
    decision = api.post(
        route,
        json={"action": "replace", "scope": "document:atlas"},
        headers={"x-csrf-token": csrf},
    )
    assert decision.status_code == 200
    assert decision.json()["decision"] == "REQUIRE_APPROVAL"
    rejected = api.post(
        route,
        json={"action": "delete", "scope": "document:atlas"},
        headers={"x-csrf-token": csrf},
    )
    assert rejected.status_code == 422
    assert rejected.json()["title"] == "tool.invalid_input"
    assert "policy.tool_effect_evaluated" in api.get("/api/v1/audit-events").text


def test_tool_version_cannot_be_read_or_evaluated_through_another_project() -> None:
    api, csrf, project_id = client()
    created = api.post(
        f"/api/v1/projects/{project_id}/tools",
        json=payload("READ"),
        headers={"x-csrf-token": csrf, "idempotency-key": "tool-v1"},
    ).json()
    other = api.post(
        "/api/v1/projects",
        json={"name": "Orion Research", "key": "ORION"},
        headers={"x-csrf-token": csrf, "idempotency-key": "create-orion"},
    ).json()
    versions = api.get(f"/api/v1/projects/{other['id']}/tools/{created['tool_id']}/versions")
    evaluation = api.post(
        f"/api/v1/projects/{other['id']}/tools/{created['tool_id']}/versions/1:evaluate",
        json={"action": "replace", "scope": "document:atlas"},
        headers={"x-csrf-token": csrf},
    )
    assert versions.status_code == 404
    assert evaluation.status_code == 404


def test_tool_mutations_require_authentication_csrf_and_known_schema() -> None:
    api, csrf, project_id = client()
    route = f"/api/v1/projects/{project_id}/tools"
    assert api.get(route, headers={"cookie": ""}).status_code == 401
    assert api.post(route, json=payload()).status_code == 403
    unknown_schema = {"$schema": "https://example.invalid/schema", "type": "object"}
    rejected = api.post(
        route,
        json={**payload("READ"), "input_schema": unknown_schema},
        headers={"x-csrf-token": csrf, "idempotency-key": "bad-schema"},
    )
    assert rejected.status_code == 422
    assert rejected.json()["title"] == "tool.invalid_input"
