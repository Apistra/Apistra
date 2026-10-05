"""Durable policy versions, idempotency, and decision audit."""

import os
from datetime import UTC, datetime, timedelta
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
from apistra.modules.policies.adapters.postgres import PostgresPolicyStore
from apistra.modules.policies.application import PolicyService
from apistra.modules.policies.domain import LimitObservation
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


def test_postgres_limit_policy_version_replay_conflict_and_audit() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """TRUNCATE limit_policy_audit_events, limit_policy_idempotency,
                      limit_policy_versions, policy_audit_events,
                      policy_approval_exceptions, tool_audit_events,
                      tool_idempotency, tool_versions,
                      project_audit_events, project_idempotency, projects,
                      identity_audit_events, identity_sessions, identity_administrators CASCADE"""
        )
    clock = UtcClock()
    identity = IdentityService(
        PostgresIdentityStore(dsn),
        Argon2PasswordHasher(),
        SecureTokenService(),
        clock,
        timedelta(hours=12),
    )
    owner = identity.bootstrap(
        "admin.alpha", "correct horse battery", "corr-bootstrap"
    ).value.administrator_id
    project = (
        ProjectService(PostgresProjectStore(dsn), clock)
        .create(owner, "admin.alpha", "Atlas Research", "ATLAS", "create-atlas", "corr-project")
        .value
    )
    service = PolicyService(PostgresPolicyStore(dsn), clock)
    args = (
        owner,
        "admin.alpha",
        project.id,
        "interactive-default",
        300,
        10,
        20_000,
        150,
        "EUR",
        2,
        30,
        60,
        None,
        "policy-v1",
        "corr-v1",
    )
    created = service.create_limit_policy_version(*args).value
    assert service.create_limit_policy_version(*args).value == created
    assert service.exact_limit_policy(owner, project.id, created.policy_id, 1).value == created
    assert service.exact_limit_policy(owner, uuid4(), created.policy_id, 1).error is not None
    second = service.create_limit_policy_version(
        owner,
        "admin.alpha",
        project.id,
        "interactive-default",
        300,
        12,
        20_000,
        150,
        "EUR",
        2,
        30,
        60,
        80,
        "policy-v2",
        "corr-v2",
        policy_id=created.policy_id,
        expected_latest_version=1,
    ).value
    assert second.version == 2 and second.status == "DRAFT"
    published = service.publish_limit_policy_version(
        owner, "admin.alpha", project.id, created.policy_id, 2, "corr-publish"
    ).value
    assert published.status == "PUBLISHED"
    assert service.exact_limit_policy(owner, project.id, created.policy_id, 1).value == created
    decision = service.evaluate_limits(
        owner,
        "admin.alpha",
        project.id,
        created.policy_id,
        1,
        LimitObservation(0, 11, 0, 0, 0, 0, 60),
        "corr-decision",
    ).value
    assert decision.decision == "DENY" and decision.action == "STOP"
    events = service.limit_audit_events(owner).value
    assert len(events) == 4
    assert events[0].details["boundaries"]["maximum_calls"] == 10
    assert events[0].created_at <= datetime.now(UTC)
