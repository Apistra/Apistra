from __future__ import annotations

import os
from datetime import timedelta

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_postgres import PostgresEndpointStore
from apistra.modules.catalog.adapters.postgres import PostgresSecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    EndpointPurpose,
    EndpointStatus,
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


class ApprovedPolicy:
    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None:
        return ApprovedDestination("http", "127.0.0.1", 18080, "/v1", ("127.0.0.1",))


class PassingProbe:
    def probe(
        self,
        protocol: ProviderProtocol,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome:
        return ProbeOutcome.CONNECTION_VERIFIED


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


def test_postgres_endpoint_create_replay_probe_and_audit() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE endpoint_audit_events, endpoint_idempotency, model_endpoints,
                     secret_audit_events, secret_idempotency, secret_references,
                     project_audit_events, project_idempotency, projects,
                     identity_audit_events, identity_sessions, identity_administrators CASCADE
            """
        )
    identity = IdentityService(
        PostgresIdentityStore(dsn),
        Argon2PasswordHasher(),
        SecureTokenService(),
        UtcClock(),
        timedelta(hours=12),
    )
    owner = identity.bootstrap(
        "admin.alpha", "correct horse battery", "corr-bootstrap"
    ).value.administrator_id
    project = (
        ProjectService(PostgresProjectStore(dsn), UtcClock())
        .create(owner, "admin.alpha", "Atlas Research", "ATLAS", "create-atlas", "corr-project")
        .value
    )
    secrets = SecretService(
        PostgresSecretStore(dsn),
        AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))}),
        UtcClock(),
        "installation-test",
    )
    reference = secrets.create(
        owner,
        "admin.alpha",
        project.id,
        "provider-primary",
        "Endpoint",
        "canary",
        "secret-key",
        "corr-secret",
    ).value
    service = EndpointService(
        PostgresEndpointStore(dsn), secrets, ApprovedPolicy(), PassingProbe(), UtcClock()
    )
    args = (
        owner,
        "admin.alpha",
        project.id,
        "local-llm",
        EndpointPurpose.GENERATIVE,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "http://127.0.0.1:18080/v1",
        "synthetic-chat",
        reference.id,
        NetworkProfile.LOCAL,
        "endpoint-key",
        "corr-endpoint",
    )
    created = service.create(*args).value
    replay = service.create(*args).value
    assert replay.id == created.id
    tested = service.test_connection(
        owner, "admin.alpha", project.id, created.id, 1, "corr-probe"
    ).value
    assert tested.status is EndpointStatus.VERIFIED
    assert tested.version == 2
    assert [event.event_type for event in service.audit_events(owner).value] == [
        "endpoint.connection_tested",
        "endpoint.created",
    ]
