from __future__ import annotations

import os
from datetime import timedelta

import psycopg
import pytest

from apistra.entrypoints.cap01_fixture import (
    ADMIN_NO_PROJECT,
    FRESH,
    ISOLATION,
    ORION_ID,
    FixtureGuardError,
    apply_fixture,
)
from apistra.entrypoints.migration import apply_migrations
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.domain import IdentityErrorCode
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.domain import ProjectErrorCode


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


def apply(dsn: str, fixture_id: str, run_id: str = "fixture-test") -> dict[str, object]:
    return apply_fixture(
        dsn,
        fixture_id,
        run_id,
        f"local-staging-{run_id}",
        f"apply-cap01-{run_id}",
        fixture_id,
        "correct horse battery" if fixture_id != FRESH else None,
    )


def test_fixture_guard_fails_before_database_access() -> None:
    with pytest.raises(FixtureGuardError, match="APISTRA_ENVIRONMENT"):
        apply_fixture(
            "postgresql://unreachable/never-used",
            FRESH,
            "guard",
            "production",
            "apply-cap01-guard",
            FRESH,
            None,
        )


def test_isolation_fixture_materialises_real_owner_boundary_and_resets() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    receipt = apply(dsn, ISOLATION)

    assert receipt["counts"] == {"administrators": 2, "projects": 2}
    identity = IdentityService(
        PostgresIdentityStore(dsn),
        Argon2PasswordHasher(),
        SecureTokenService(),
        UtcClock(),
        timedelta(hours=12),
    )
    signed_in = identity.authenticate("admin.alpha", "correct horse battery", "fixture-sign-in")
    assert signed_in.succeeded
    disabled = identity.authenticate(
        "fixture.orion.owner", "not-a-real-credential", "fixture-disabled"
    )
    assert disabled.error.code is IdentityErrorCode.INVALID_CREDENTIALS

    projects = ProjectService(PostgresProjectStore(dsn), UtcClock())
    owner_id = signed_in.value.administrator_id
    listed = projects.list(owner_id).value
    assert [(project.name, project.key) for project in listed] == [("Atlas Research", "ATLAS")]
    assert projects.get(owner_id, ORION_ID).error.code is ProjectErrorCode.NOT_FOUND

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT login_enabled FROM identity_administrators WHERE username = %s",
            ("fixture.orion.owner",),
        )
        assert cursor.fetchone()[0] is False

    assert apply(dsn, FRESH)["counts"] == {"administrators": 0, "projects": 0}


def test_administrator_fixture_is_repeatable_and_contains_no_project() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    first = apply(dsn, ADMIN_NO_PROJECT)
    second = apply(dsn, ADMIN_NO_PROJECT)
    assert (
        first["counts"]
        == second["counts"]
        == {
            "administrators": 1,
            "projects": 0,
        }
    )
