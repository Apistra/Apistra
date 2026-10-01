"""Apply deterministic CAP-01 state only to an explicitly isolated local staging database."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
from datetime import UTC, datetime
from uuid import UUID

import psycopg

from apistra.entrypoints.fixture.composition import build_fixture_password_hasher

FIXTURE_REVISION = "CAP-01-FX-0.2"
FRESH = "FX-PRC-01-FRESH"
ADMIN_NO_PROJECT = "FX-PRC-01-ADMIN-NO-PROJECT"
ISOLATION = "FX-PRC-01-ISOLATION"
FIXTURE_IDS = (FRESH, ADMIN_NO_PROJECT, ISOLATION)

ADMIN_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
FOREIGN_OWNER_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
ATLAS_ID = UUID("11111111-1111-4111-8111-111111111111")
ORION_ID = UUID("22222222-2222-4222-8222-222222222222")
FIXTURE_LOCK_ID = 2_029_100_100_002


class FixtureGuardError(RuntimeError):
    """Raised before any database connection when fixture safeguards do not match."""


def _guard(environment: str, gate: str, run_id: str, confirmation: str) -> None:
    expected_environment = f"local-staging-{run_id}"
    expected_gate = f"apply-cap01-{run_id}"
    if environment != expected_environment:
        raise FixtureGuardError(f"APISTRA_ENVIRONMENT must equal {expected_environment!r}.")
    if gate != expected_gate:
        raise FixtureGuardError("APISTRA_FIXTURE_GATE does not authorise this run ID.")
    if confirmation not in FIXTURE_IDS:
        raise FixtureGuardError("--confirm-reset must name the selected CAP-01 fixture.")


def _insert_administrator(
    cursor,
    *,
    administrator_id: UUID,
    username: str,
    password_hash: str,
    created_at: datetime,
    login_enabled: bool,
) -> None:
    cursor.execute(
        """
        INSERT INTO identity_administrators
            (id, installation_id, username, password_hash, created_at, login_enabled)
        VALUES (%s, 'local', %s, %s, %s, %s)
        """,
        (administrator_id, username, password_hash, created_at, login_enabled),
    )


def _insert_project(
    cursor,
    *,
    project_id: UUID,
    owner_id: UUID,
    name: str,
    key: str,
    created_at: datetime,
) -> None:
    cursor.execute(
        """
        INSERT INTO projects
            (id, owner_administrator_id, name, project_key, status,
             version, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 'ACTIVE', 1, %s, %s)
        """,
        (project_id, owner_id, name, key, created_at, created_at),
    )


def apply_fixture(
    dsn: str,
    fixture_id: str,
    run_id: str,
    environment: str,
    gate: str,
    confirmation: str,
    administrator_password: str | None,
) -> dict[str, object]:
    """Reset and seed one isolated database after all fail-closed guards pass."""

    _guard(environment, gate, run_id, confirmation)
    if fixture_id != confirmation:
        raise FixtureGuardError("Fixture and reset confirmation do not match.")
    if fixture_id != FRESH and not administrator_password:
        raise FixtureGuardError("STAGING_ADMIN_PASSWORD is required for this fixture.")

    applied_at = datetime.now(UTC)
    hasher = build_fixture_password_hasher()
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", (FIXTURE_LOCK_ID,))
        cursor.execute(
            """
            TRUNCATE project_audit_events, project_idempotency, projects,
                     identity_audit_events, identity_sessions,
                     identity_administrators CASCADE
            """
        )
        if fixture_id != FRESH:
            _insert_administrator(
                cursor,
                administrator_id=ADMIN_ID,
                username="admin.alpha",
                password_hash=hasher.hash(administrator_password or ""),
                created_at=applied_at,
                login_enabled=True,
            )
        if fixture_id == ISOLATION:
            _insert_administrator(
                cursor,
                administrator_id=FOREIGN_OWNER_ID,
                username="fixture.orion.owner",
                password_hash=hasher.hash(secrets.token_urlsafe(48)),
                created_at=applied_at,
                login_enabled=False,
            )
            _insert_project(
                cursor,
                project_id=ATLAS_ID,
                owner_id=ADMIN_ID,
                name="Atlas Research",
                key="ATLAS",
                created_at=applied_at,
            )
            _insert_project(
                cursor,
                project_id=ORION_ID,
                owner_id=FOREIGN_OWNER_ID,
                name="Orion Restricted",
                key="ORION",
                created_at=applied_at,
            )
        cursor.execute("SELECT COUNT(*) FROM identity_administrators")
        administrator_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]

    identity = f"{FIXTURE_REVISION}:{fixture_id}:{run_id}"
    return {
        "status": "APPLIED",
        "target": "isolated-local-staging",
        "environment": environment,
        "run_id": run_id,
        "fixture_id": fixture_id,
        "fixture_revision": FIXTURE_REVISION,
        "fixture_identity_sha256": hashlib.sha256(identity.encode()).hexdigest(),
        "applied_at": applied_at.isoformat(),
        "counts": {
            "administrators": administrator_count,
            "projects": project_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_id", choices=FIXTURE_IDS)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--confirm-reset", required=True)
    args = parser.parse_args()

    try:
        receipt = apply_fixture(
            os.environ["APISTRA_DATABASE_URL"],
            args.fixture_id,
            args.run_id,
            os.getenv("APISTRA_ENVIRONMENT", ""),
            os.getenv("APISTRA_FIXTURE_GATE", ""),
            args.confirm_reset,
            os.getenv("STAGING_ADMIN_PASSWORD"),
        )
    except (FixtureGuardError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
