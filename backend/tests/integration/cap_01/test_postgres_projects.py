from __future__ import annotations

import os
from datetime import timedelta
from uuid import uuid4

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.projects.adapters.postgres import (
    PostgresProjectStore,
    count_project_rows,
)
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.domain import ProjectErrorCode


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


@pytest.fixture
def owner_and_service() -> tuple[str, object, ProjectService]:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE project_audit_events, project_idempotency, projects,
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
    administrator = identity.bootstrap(
        "admin.alpha", "correct horse battery", "corr-bootstrap"
    ).value
    return (
        dsn,
        administrator.administrator_id,
        ProjectService(PostgresProjectStore(dsn), UtcClock()),
    )


def test_postgres_project_lifecycle_and_idempotency(owner_and_service) -> None:
    dsn, owner, projects = owner_and_service
    created = projects.create(
        owner, "admin.alpha", "Atlas Research", "ATLAS", "idem", "corr-create"
    )
    replay = projects.create(owner, "admin.alpha", "Atlas Research", "ATLAS", "idem", "corr-replay")
    assert replay.value.id == created.value.id
    updated = projects.update(
        owner, "admin.alpha", created.value.id, 1, "Atlas Platform", "ATLAS-2", "corr-update"
    )
    assert updated.value.version == 2
    assert projects.archive(owner, "admin.alpha", created.value.id, 2, "corr-archive").succeeded
    assert count_project_rows(dsn) == {
        "projects": 1,
        "idempotency": 1,
        "audit_events": 3,
    }


def test_postgres_owner_and_version_checks_do_not_change_state(owner_and_service) -> None:
    _dsn, owner, projects = owner_and_service
    created = projects.create(owner, "admin.alpha", "Atlas Research", "ATLAS", "idem", "corr").value
    assert projects.get(uuid4(), created.id).error.code is ProjectErrorCode.NOT_FOUND
    stale = projects.update(owner, "admin.alpha", created.id, 9, "Stale", "STALE", "corr")
    assert stale.error.code is ProjectErrorCode.VERSION_CONFLICT
    assert projects.get(owner, created.id).value.name == "Atlas Research"
