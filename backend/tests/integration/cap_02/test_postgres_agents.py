from __future__ import annotations

import os
from datetime import timedelta

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.agents.adapters.postgres import PostgresAgentStore
from apistra.modules.agents.application import AgentService
from apistra.modules.agents.domain import AgentVersionStatus, VersionReference
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_postgres import PostgresEndpointStore
from apistra.modules.catalog.adapters.postgres import PostgresSecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    EndpointPurpose,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService


class Policy:
    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None:
        return None


class Probe:
    def probe(
        self,
        protocol: ProviderProtocol,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome:
        raise AssertionError("agent creation must not probe")


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for PostgreSQL integration")
    return value


def test_postgres_agent_versions_are_immutable_scoped_idempotent_and_audited() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """TRUNCATE agent_audit_events, agent_idempotency, agent_versions,
            endpoint_audit_events, endpoint_idempotency, model_endpoints,
            secret_audit_events, secret_idempotency, secret_references,
            project_audit_events, project_idempotency, projects,
            identity_audit_events, identity_sessions, identity_administrators CASCADE"""
        )
    clock = UtcClock()
    owner = (
        IdentityService(
            PostgresIdentityStore(dsn),
            Argon2PasswordHasher(),
            SecureTokenService(),
            clock,
            timedelta(hours=12),
        )
        .bootstrap("admin.alpha", "correct horse battery", "bootstrap")
        .value.administrator_id
    )
    project = (
        ProjectService(PostgresProjectStore(dsn), clock)
        .create(owner, "admin.alpha", "Atlas Research", "ATLAS", "project", "project-corr")
        .value
    )
    secrets = SecretService(
        PostgresSecretStore(dsn),
        AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))}),
        clock,
        "installation-test",
    )
    secret = secrets.create(
        owner,
        "admin.alpha",
        project.id,
        "provider-primary",
        "Endpoint",
        "canary",
        "secret",
        "secret-corr",
    ).value
    endpoints = EndpointService(PostgresEndpointStore(dsn), secrets, Policy(), Probe(), clock)
    endpoint = endpoints.create(
        owner,
        "admin.alpha",
        project.id,
        "local-llm",
        EndpointPurpose.GENERATIVE,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "http://127.0.0.1:18080/v1",
        "model",
        secret.id,
        NetworkProfile.LOCAL,
        "endpoint",
        "endpoint-corr",
    ).value
    service = AgentService(PostgresAgentStore(dsn), endpoints, clock)
    reference = VersionReference(endpoint.id, endpoint.version)
    first = service.create_version(
        owner,
        "admin.alpha",
        project.id,
        "Research Analyst",
        "v1",
        reference,
        None,
        (),
        None,
        "agent-v1",
        "agent-corr",
    ).value
    replay = service.create_version(
        owner,
        "admin.alpha",
        project.id,
        "Research Analyst",
        "v1",
        reference,
        None,
        (),
        None,
        "agent-v1",
        "agent-corr",
    ).value
    second = service.create_version(
        owner,
        "admin.alpha",
        project.id,
        "Research Analyst",
        "v2",
        reference,
        None,
        (),
        None,
        "agent-v2",
        "agent-corr-2",
        agent_id=first.agent_id,
        expected_latest_version=1,
    ).value
    assert replay == first
    assert second.status is AgentVersionStatus.DRAFT
    assert [item.version for item in service.versions(owner, project.id, first.agent_id).value] == [
        2,
        1,
    ]
    assert service.list(owner, project.id).value == [second]
    assert [event.agent_version for event in service.audit_events(owner).value] == [2, 1]
