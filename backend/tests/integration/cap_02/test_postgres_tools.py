from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest

from apistra.entrypoints.migration import apply_migrations
from apistra.modules.catalog.adapters.tool_postgres import PostgresToolStore
from apistra.modules.catalog.application.tools import JSON_SCHEMA_DIALECT, ToolService
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.policies.adapters.postgres import PostgresPolicyStore
from apistra.modules.policies.application import PolicyService
from apistra.modules.policies.domain import ApprovalException, EffectClass
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService

SCHEMA = {"$schema": JSON_SCHEMA_DIALECT, "type": "object"}


def database_url() -> str:
    value = os.getenv("APISTRA_TEST_DATABASE_URL")
    if not value:
        pytest.skip("APISTRA_TEST_DATABASE_URL is required for the PostgreSQL integration test")
    return value


def test_postgres_tool_versions_exact_policy_exception_and_audit() -> None:
    dsn = database_url()
    apply_migrations(dsn)
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            TRUNCATE policy_audit_events, policy_approval_exceptions,
                     tool_audit_events, tool_idempotency, tool_versions,
                     project_audit_events, project_idempotency, projects,
                     identity_audit_events, identity_sessions, identity_administrators CASCADE
            """
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
    tools = ToolService(PostgresToolStore(dsn), clock)
    args = (
        owner,
        "admin.alpha",
        project.id,
        "document-write",
        "Replace a document.",
        SCHEMA,
        SCHEMA,
        "WRITE",
        ("replace",),
        "tool-v1",
        "corr-tool",
    )
    created = tools.create_version(*args).value
    replay = tools.create_version(*args).value
    assert replay == created
    assert tools.exact(owner, project.id, created.tool_id, 1).value == created
    second = tools.create_version(
        owner,
        "admin.alpha",
        project.id,
        "document-write",
        "Replace a document with approval.",
        SCHEMA,
        SCHEMA,
        "WRITE",
        ("replace",),
        "tool-v2",
        "corr-tool-v2",
        tool_id=created.tool_id,
        expected_latest_version=1,
    ).value
    assert second.version == 2

    policy_store = PostgresPolicyStore(dsn)
    policies = PolicyService(policy_store, clock)
    before = policies.evaluate(
        owner,
        "admin.alpha",
        project.id,
        created.tool_id,
        1,
        EffectClass.WRITE,
        "replace",
        "document:atlas",
        "corr-before",
    ).value
    exception = ApprovalException(
        uuid4(),
        owner,
        project.id,
        created.tool_id,
        1,
        "replace",
        "document:atlas",
        datetime.now(UTC) + timedelta(hours=1),
        True,
    )
    policy_store.add_exception(exception)
    after = policies.evaluate(
        owner,
        "admin.alpha",
        project.id,
        created.tool_id,
        1,
        EffectClass.WRITE,
        "replace",
        "document:atlas",
        "corr-after",
    ).value
    wrong_version = policies.evaluate(
        owner,
        "admin.alpha",
        project.id,
        created.tool_id,
        2,
        EffectClass.WRITE,
        "replace",
        "document:atlas",
        "corr-wrong-version",
    ).value
    assert before.decision == "REQUIRE_APPROVAL"
    assert after.decision == "ALLOW" and after.exception_id == exception.id
    assert wrong_version.decision == "REQUIRE_APPROVAL"
    assert len(tools.audit_events(owner).value) == 2
    assert len(policies.audit_events(owner).value) == 3
