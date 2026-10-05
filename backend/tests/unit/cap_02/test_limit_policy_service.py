"""Exact resource decisions and fail-closed policy-version invariants."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apistra.modules.policies.adapters.memory import InMemoryPolicyStore
from apistra.modules.policies.application import PolicyService
from apistra.modules.policies.domain import LimitObservation, PolicyErrorCode


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 5, 10, tzinfo=UTC)


def create_policy(service: PolicyService, owner, project):
    return service.create_limit_policy_version(
        owner,
        "admin.alpha",
        project,
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
        "corr-create",
    ).value


def observation(**overrides: int) -> LimitObservation:
    values = {
        "duration_seconds": 0,
        "calls": 0,
        "tokens": 0,
        "cost_minor_units": 0,
        "concurrency": 0,
        "requests_in_window": 0,
        "rate_window_seconds": 60,
    }
    values.update(overrides)
    return LimitObservation(**values)


@pytest.mark.parametrize(
    ("observed", "decision", "effect_count"),
    [(9, "ALLOW", 1), (10, "ALLOW", 1), (11, "DENY", 0)],
)
def test_exact_call_boundary_gates_effect(observed, decision, effect_count) -> None:
    owner, project = uuid4(), uuid4()
    store = InMemoryPolicyStore()
    service = PolicyService(store, Clock())
    policy = create_policy(service, owner, project)
    effects: list[str] = []
    result = service.evaluate_limits(
        owner,
        "admin.alpha",
        project,
        policy.policy_id,
        policy.version,
        observation(calls=observed),
        f"corr-{observed}",
        lambda: effects.append("model-called"),
    ).value
    assert result.decision == decision
    assert result.action == ("STOP" if decision == "DENY" else "ALLOW")
    assert len(effects) == effect_count
    event = store.limit_audit_events[-1]
    assert event.policy_version == 1
    assert event.details["boundaries"]["maximum_calls"] == 10
    assert event.details["observed"]["maximum_calls"] == observed
    assert event.correlation_id == f"corr-{observed}"


@pytest.mark.parametrize(
    ("observed", "limit"),
    [
        ({"duration_seconds": 301}, "maximum_duration"),
        ({"tokens": 20_001}, "maximum_tokens"),
        ({"cost_minor_units": 151}, "maximum_cost"),
        ({"concurrency": 3}, "maximum_concurrency"),
        ({"requests_in_window": 31}, "rate_limit"),
    ],
)
def test_every_hard_boundary_denies_without_effect(observed, limit) -> None:
    owner, project = uuid4(), uuid4()
    service = PolicyService(InMemoryPolicyStore(), Clock())
    policy = create_policy(service, owner, project)
    effects: list[str] = []
    result = service.evaluate_limits(
        owner,
        "admin.alpha",
        project,
        policy.policy_id,
        1,
        observation(**observed),
        "corr-denial",
        lambda: effects.append("connector-called"),
    ).value
    assert result.decision == "DENY"
    assert result.violated_limits == (limit,)
    assert effects == []


def test_version_replay_conflict_scope_and_warning() -> None:
    owner, project, foreign = uuid4(), uuid4(), uuid4()
    store = InMemoryPolicyStore()
    service = PolicyService(store, Clock())
    policy = create_policy(service, owner, project)
    replay = create_policy(service, owner, project)
    assert replay == policy
    assert len(store.limit_audit_events) == 1
    assert service.exact_limit_policy(owner, foreign, policy.policy_id, 1).error.code == (
        PolicyErrorCode.UNAVAILABLE
    )
    changed = service.create_limit_policy_version(
        owner,
        "admin.alpha",
        project,
        "changed",
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
        "corr-conflict",
    )
    assert changed.error.code == PolicyErrorCode.IDEMPOTENCY_CONFLICT
    draft = service.create_limit_policy_version(
        owner,
        "admin.alpha",
        project,
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
        policy_id=policy.policy_id,
        expected_latest_version=1,
    ).value
    assert draft.status == "DRAFT" and draft.version == 2
    assert service.exact_limit_policy(owner, project, policy.policy_id, 1).value == policy
    assert not service.exact_limit_policy_available(owner, project, policy.policy_id, 2)
    assert (
        service.evaluate_limits(
            owner, "admin.alpha", project, policy.policy_id, 2, observation(calls=10), "corr-draft"
        ).error.code
        == PolicyErrorCode.UNAVAILABLE
    )
    published = service.publish_limit_policy_version(
        owner, "admin.alpha", project, policy.policy_id, 2, "corr-publish"
    ).value
    assert published.status == "PUBLISHED"
    assert service.exact_limit_policy_available(owner, project, policy.policy_id, 2)
    warning = service.evaluate_limits(
        owner,
        "admin.alpha",
        project,
        policy.policy_id,
        2,
        observation(calls=10),
        "corr-warn",
    ).value
    assert warning.decision == "WARN"
    stale = service.create_limit_policy_version(
        owner,
        "admin.alpha",
        project,
        "interactive-default",
        300,
        12,
        20_000,
        150,
        "EUR",
        2,
        30,
        60,
        None,
        "policy-v3",
        "corr-stale",
        policy_id=policy.policy_id,
        expected_latest_version=1,
    )
    assert stale.error.code == PolicyErrorCode.VERSION_CONFLICT
    assert len(service.limit_policy_versions(owner, project, policy.policy_id).value) == 2


def test_invalid_policy_and_rate_window_do_not_emit_decision() -> None:
    owner, project = uuid4(), uuid4()
    store = InMemoryPolicyStore()
    service = PolicyService(store, Clock())
    policy = create_policy(service, owner, project)
    bad = service.evaluate_limits(
        owner,
        "admin.alpha",
        project,
        policy.policy_id,
        1,
        observation(rate_window_seconds=30),
        "corr-invalid",
    )
    assert bad.error.code == PolicyErrorCode.INVALID_INPUT
    assert len(store.limit_audit_events) == 1
