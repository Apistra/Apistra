from __future__ import annotations

import os
from datetime import timedelta
from uuid import uuid4

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.postgres import PostgresSecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.domain import SecretErrorCode
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


@pytest.fixture
def owner_project_and_service() -> tuple[object, object, SecretService]:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE secret_audit_events, secret_idempotency, secret_references,
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
    return owner, project.id, secrets


def test_postgres_secret_lifecycle_and_owner_scope(owner_project_and_service) -> None:
    owner, project_id, secrets = owner_project_and_service
    created = secrets.create(
        owner,
        "admin.alpha",
        project_id,
        "provider-primary",
        "Primary endpoint credential",
        "postgres-canary",
        "create-primary",
        "corr-create",
    )
    replay = secrets.create(
        owner,
        "admin.alpha",
        project_id,
        "provider-primary",
        "Primary endpoint credential",
        "postgres-canary",
        "create-primary",
        "corr-replay",
    )
    assert replay.value.id == created.value.id
    assert secrets.resolve(owner, project_id, created.value.id).value.value == b"postgres-canary"
    assert secrets.resolve(uuid4(), project_id, created.value.id).error.code is (
        SecretErrorCode.UNAVAILABLE
    )
    replaced = secrets.replace(
        owner,
        "admin.alpha",
        project_id,
        created.value.id,
        1,
        "postgres-rotated",
        "corr-replace",
    )
    assert replaced.value.version == 2
    assert [event.event_type for event in secrets.audit_events(owner).value] == [
        "secret.replaced",
        "secret.created",
    ]
