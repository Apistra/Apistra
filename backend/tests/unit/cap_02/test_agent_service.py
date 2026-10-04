from datetime import UTC, datetime
from uuid import UUID, uuid4

from apistra.modules.agents.adapters.memory import InMemoryAgentStore
from apistra.modules.agents.application import AgentService
from apistra.modules.agents.domain import AgentVersionStatus, VersionReference
from apistra.modules.catalog.adapters.endpoint_memory import InMemoryEndpointStore
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain.endpoints import (
    EndpointPurpose,
    EndpointStatus,
    ModelEndpoint,
    NetworkProfile,
    ProviderProtocol,
)

OWNER = UUID("00000000-0000-0000-0000-000000000001")
PROJECT = UUID("00000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 10, 4, 20, tzinfo=UTC)


class Clock:
    def now(self) -> datetime:
        return NOW


class Unused:
    def __getattr__(self, name: str):
        raise AssertionError(name)


def endpoint(store: InMemoryEndpointStore, name: str) -> VersionReference:
    endpoint_id = uuid4()
    value = ModelEndpoint(
        endpoint_id,
        OWNER,
        PROJECT,
        name,
        EndpointPurpose.GENERATIVE,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "https://example.com/v1",
        "model",
        uuid4(),
        NetworkProfile.CLOUD,
        EndpointStatus.UNVERIFIED,
        1,
        None,
        NOW,
        NOW,
    )
    from apistra.modules.catalog.domain.endpoints import EndpointAuditEvent

    event = EndpointAuditEvent(
        uuid4(), "endpoint.created", NOW, "corr", OWNER, "admin", PROJECT, endpoint_id
    )
    assert store.create(value, event, name, name)[0]
    return VersionReference(endpoint_id, 1)


def service() -> tuple[AgentService, VersionReference, VersionReference]:
    endpoint_store = InMemoryEndpointStore()
    endpoints = EndpointService(endpoint_store, Unused(), Unused(), Unused(), Clock())
    return (
        AgentService(InMemoryAgentStore(), endpoints, Clock()),
        endpoint(endpoint_store, "primary"),
        endpoint(endpoint_store, "fallback"),
    )


def test_first_version_is_published_idempotent_and_routes_only_declared_endpoints() -> None:
    agents, primary, fallback = service()
    args = (
        OWNER,
        "admin.alpha",
        PROJECT,
        "Research Analyst",
        "Use evidence.",
        primary,
        fallback,
        (),
        None,
        "key-1",
        "corr-1",
    )
    created = agents.create_version(*args).value
    replay = agents.create_version(*args).value
    assert created == replay
    assert created.status is AgentVersionStatus.PUBLISHED
    assert created.ordered_endpoints() == (primary, fallback)


def test_edit_creates_new_draft_and_preserves_published_version() -> None:
    agents, primary, fallback = service()
    first = agents.create_version(
        OWNER,
        "admin.alpha",
        PROJECT,
        "Research Analyst",
        "v1",
        primary,
        fallback,
        (),
        None,
        "key-1",
        "corr-1",
    ).value
    second = agents.create_version(
        OWNER,
        "admin.alpha",
        PROJECT,
        "Research Analyst",
        "v2",
        primary,
        None,
        (),
        None,
        "key-2",
        "corr-2",
        agent_id=first.agent_id,
        expected_latest_version=1,
    ).value
    versions = agents.versions(OWNER, PROJECT, first.agent_id).value
    assert second.status is AgentVersionStatus.DRAFT
    assert [item.instructions for item in versions] == ["v2", "v1"]
    assert versions[1].status is AgentVersionStatus.PUBLISHED
    assert second.ordered_endpoints() == (primary,)


def test_foreign_stale_and_duplicate_endpoint_references_are_rejected() -> None:
    agents, primary, _fallback = service()
    stale = VersionReference(primary.id, 99)
    duplicate = agents.create_version(
        OWNER, "admin", PROJECT, "A", "B", primary, primary, (), None, "key", "corr"
    )
    foreign = agents.create_version(
        OWNER, "admin", PROJECT, "A", "B", stale, None, (), None, "key-2", "corr"
    )
    assert duplicate.error.code == "agent.invalid_input"
    assert foreign.error.code == "agent.invalid_input"


def test_input_idempotency_version_and_unavailable_failures_are_explicit() -> None:
    agents, primary, _fallback = service()
    empty_name = agents.create_version(
        OWNER, "admin", PROJECT, "", "instructions", primary, None, (), None, "key-1", "corr"
    )
    empty_instructions = agents.create_version(
        OWNER, "admin", PROJECT, "Agent", "", primary, None, (), None, "key-2", "corr"
    )
    empty_key = agents.create_version(
        OWNER, "admin", PROJECT, "Agent", "instructions", primary, None, (), None, "", "corr"
    )
    first = agents.create_version(
        OWNER, "admin", PROJECT, "Agent", "v1", primary, None, (), None, "key-3", "corr"
    ).value
    idempotency_conflict = agents.create_version(
        OWNER, "admin", PROJECT, "Agent", "different", primary, None, (), None, "key-3", "corr"
    )
    version_conflict = agents.create_version(
        OWNER,
        "admin",
        PROJECT,
        "Agent",
        "v2",
        primary,
        None,
        (),
        None,
        "key-4",
        "corr",
        agent_id=first.agent_id,
        expected_latest_version=9,
    )
    unavailable = agents.versions(OWNER, PROJECT, uuid4())
    assert empty_name.error.code == "agent.invalid_input"
    assert empty_instructions.error.code == "agent.invalid_input"
    assert empty_key.error.code == "agent.invalid_input"
    assert idempotency_conflict.error.code == "agent.idempotency_conflict"
    assert version_conflict.error.code == "agent.version_conflict"
    assert unavailable.error.code == "agent.unavailable"


def test_public_boundary_exports_agent_contract() -> None:
    from apistra.modules.agents import public

    assert public.AgentService is AgentService
    assert public.VersionReference is VersionReference
