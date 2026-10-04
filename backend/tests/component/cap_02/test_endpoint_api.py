from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apistra.entrypoints.api.main import create_app
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_memory import InMemoryEndpointStore
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.platform.runtime import RuntimeSettings


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 4, 18, tzinfo=UTC)


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


class BlockingPolicy:
    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None:
        return None


class UnusedProbe:
    def probe(
        self,
        protocol: ProviderProtocol,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome:
        raise AssertionError("blocked destinations must never reach the probe")


def client() -> tuple[TestClient, str, str, str]:
    identity = IdentityService(
        InMemoryIdentityStore(), Hasher(), Tokens(), Clock(), timedelta(hours=12)
    )
    projects = ProjectService(InMemoryProjectStore(), Clock())
    secrets = SecretService(
        InMemorySecretStore(),
        AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))}),
        Clock(),
        "installation-test",
    )
    endpoints = EndpointService(
        InMemoryEndpointStore(), secrets, BlockingPolicy(), UnusedProbe(), Clock()
    )
    api = TestClient(
        create_app(
            RuntimeSettings("api", "0.2.0", "commit", "test"),
            identity,
            projects,
            secrets,
            endpoints,
        ),
        base_url="https://testserver",
    )
    session = api.post(
        "/api/v1/administrators:bootstrap",
        json={"username": "admin.alpha", "password": "correct horse battery"},
    ).json()
    csrf = session["csrf_token"]
    project = api.post(
        "/api/v1/projects",
        json={"name": "Atlas Research", "key": "ATLAS"},
        headers={"x-csrf-token": csrf, "idempotency-key": "create-atlas"},
    ).json()
    secret = api.post(
        f"/api/v1/projects/{project['id']}/secrets",
        json={"name": "provider-primary", "purpose": "Endpoint", "value": "canary"},
        headers={"x-csrf-token": csrf, "idempotency-key": "create-secret"},
    ).json()
    return api, csrf, project["id"], secret["id"]


def test_endpoint_lifecycle_is_project_scoped_versioned_and_audited() -> None:
    api, csrf, project_id, secret_id = client()
    payload = {
        "name": "local-llm",
        "purpose": "GENERATIVE",
        "provider_protocol": "OPENAI_COMPATIBLE",
        "base_url": "http://127.0.0.1:18080/v1",
        "model_identifier": "synthetic-chat",
        "secret_reference_id": secret_id,
        "network_profile": "LOCAL",
    }
    headers = {"x-csrf-token": csrf, "idempotency-key": "create-local-llm"}
    created = api.post(f"/api/v1/projects/{project_id}/endpoints", json=payload, headers=headers)
    replay = api.post(f"/api/v1/projects/{project_id}/endpoints", json=payload, headers=headers)
    assert created.status_code == replay.status_code == 201
    assert created.json()["id"] == replay.json()["id"]
    assert created.json()["status"] == "UNVERIFIED"
    assert created.headers["etag"] == '"1"'

    listed = api.get(f"/api/v1/projects/{project_id}/endpoints")
    assert listed.status_code == 200 and len(listed.json()["items"]) == 1
    tested = api.post(
        f"/api/v1/projects/{project_id}/endpoints/{created.json()['id']}:test",
        headers={"x-csrf-token": csrf, "if-match": '"1"'},
    )
    assert tested.status_code == 200
    assert tested.json()["last_probe_outcome"] == "DESTINATION_BLOCKED"
    assert tested.json()["status"] == "UNVERIFIED"
    assert tested.headers["etag"] == '"2"'
    assert "endpoint.created" in api.get("/api/v1/audit-events").text
    assert "endpoint.connection_tested" in api.get("/api/v1/audit-events").text


def test_endpoint_requests_require_authentication_csrf_and_current_version() -> None:
    api, csrf, project_id, secret_id = client()
    payload = {
        "name": "local-llm",
        "purpose": "GENERATIVE",
        "provider_protocol": "OPENAI_COMPATIBLE",
        "base_url": "http://127.0.0.1:18080/v1",
        "model_identifier": "synthetic-chat",
        "secret_reference_id": secret_id,
        "network_profile": "LOCAL",
    }
    assert (
        api.get(f"/api/v1/projects/{project_id}/endpoints", headers={"cookie": ""}).status_code
        == 401
    )
    assert api.post(f"/api/v1/projects/{project_id}/endpoints", json=payload).status_code == 403
    created = api.post(
        f"/api/v1/projects/{project_id}/endpoints",
        json=payload,
        headers={"x-csrf-token": csrf, "idempotency-key": "create-local-llm"},
    ).json()
    missing_version = api.post(
        f"/api/v1/projects/{project_id}/endpoints/{created['id']}:test",
        headers={"x-csrf-token": csrf},
    )
    assert missing_version.status_code == 422


def test_agent_versions_retain_exact_declared_endpoint_order() -> None:
    api, csrf, project_id, secret_id = client()
    endpoint_payload = {
        "name": "primary-llm",
        "purpose": "GENERATIVE",
        "provider_protocol": "OPENAI_COMPATIBLE",
        "base_url": "http://127.0.0.1:18080/v1",
        "model_identifier": "synthetic-chat",
        "secret_reference_id": secret_id,
        "network_profile": "LOCAL",
    }
    primary = api.post(
        f"/api/v1/projects/{project_id}/endpoints",
        json=endpoint_payload,
        headers={"x-csrf-token": csrf, "idempotency-key": "primary-endpoint"},
    ).json()
    fallback = api.post(
        f"/api/v1/projects/{project_id}/endpoints",
        json={**endpoint_payload, "name": "fallback-llm"},
        headers={"x-csrf-token": csrf, "idempotency-key": "fallback-endpoint"},
    ).json()
    payload = {
        "name": "Research Analyst",
        "instructions": "Use cited evidence.",
        "primary_endpoint": {"id": primary["id"], "version": primary["version"]},
        "fallback_endpoint": {"id": fallback["id"], "version": fallback["version"]},
        "tool_versions": [],
        "limits_policy_version": None,
    }
    created = api.post(
        f"/api/v1/projects/{project_id}/agents",
        json=payload,
        headers={"x-csrf-token": csrf, "idempotency-key": "agent-v1"},
    )
    replay = api.post(
        f"/api/v1/projects/{project_id}/agents",
        json=payload,
        headers={"x-csrf-token": csrf, "idempotency-key": "agent-v1"},
    )
    assert created.status_code == replay.status_code == 201
    assert created.json() == replay.json()
    assert created.json()["status"] == "PUBLISHED"
    draft = api.post(
        f"/api/v1/projects/{project_id}/agents/{created.json()['agent_id']}/versions",
        json={**payload, "instructions": "Use verified cited evidence."},
        headers={"x-csrf-token": csrf, "idempotency-key": "agent-v2", "if-match": '"1"'},
    )
    assert draft.status_code == 201
    assert draft.json()["status"] == "DRAFT"
    versions = api.get(
        f"/api/v1/projects/{project_id}/agents/{created.json()['agent_id']}/versions"
    ).json()["items"]
    assert [item["version"] for item in versions] == [2, 1]
    assert versions[1]["primary_endpoint"] == payload["primary_endpoint"]
