from __future__ import annotations

import os
from datetime import timedelta

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore, count_identity_rows
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.domain import IdentityErrorCode


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


@pytest.fixture
def clean_database() -> str:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            "TRUNCATE identity_audit_events, identity_sessions, identity_administrators CASCADE"
        )
    return dsn


@pytest.mark.migration
def test_cap01_migration_is_idempotent(clean_database: str) -> None:
    assert apply_migrations(clean_database) == []
    assert apply_migrations(clean_database) == []


def test_postgres_round_trip_persists_only_hashes_and_audit(clean_database: str) -> None:
    service = IdentityService(
        PostgresIdentityStore(clean_database),
        Argon2PasswordHasher(),
        SecureTokenService(),
        UtcClock(),
        timedelta(hours=12),
    )
    created = service.bootstrap("administrator", "correct horse battery", "corr-bootstrap")
    assert created.succeeded
    assert service.verify_session(created.value.raw_token).succeeded
    assert service.revoke_session(
        created.value.raw_token,
        created.value.csrf_token,
        "corr-revoke",
    ).succeeded
    assert (
        service.verify_session(created.value.raw_token).error.code
        is IdentityErrorCode.SESSION_INVALID
    )
    assert count_identity_rows(clean_database) == {
        "administrators": 1,
        "sessions": 1,
        "audit_events": 2,
    }

    with psycopg.connect(clean_database) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT password_hash FROM identity_administrators")
        assert cursor.fetchone()[0].startswith("$argon2id$")
        cursor.execute("SELECT token_hash, csrf_hash FROM identity_sessions")
        token_hash, csrf_hash = cursor.fetchone()
        assert len(token_hash) == len(csrf_hash) == 64
        assert created.value.raw_token not in {token_hash, csrf_hash}
        assert created.value.csrf_token not in {token_hash, csrf_hash}
