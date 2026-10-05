from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from apistra.modules.catalog.adapters.tool_memory import InMemoryToolStore
from apistra.modules.catalog.application.tools import JSON_SCHEMA_DIALECT, ToolService
from apistra.modules.catalog.domain.tools import ToolVersionStatus
from apistra.modules.policies.adapters.memory import InMemoryPolicyStore
from apistra.modules.policies.application import PolicyService
from apistra.modules.policies.domain import ApprovalException, EffectClass

OWNER = UUID("00000000-0000-0000-0000-000000000001")
PROJECT = UUID("00000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 10, 5, 6, tzinfo=UTC)
SCHEMA = {"$schema": JSON_SCHEMA_DIALECT, "type": "object"}


class Clock:
    def now(self) -> datetime:
        return NOW


def create_tool(service: ToolService, effect: str = "WRITE"):
    return service.create_version(
        OWNER,
        "admin.alpha",
        PROJECT,
        "document-write",
        "Replace a document.",
        SCHEMA,
        SCHEMA,
        effect,
        ("replace",),
        "tool-key",
        "corr",
    )


def test_tool_version_is_immutable_idempotent_and_schema_versioned() -> None:
    service = ToolService(InMemoryToolStore(), Clock())
    first = create_tool(service).value
    replay = create_tool(service).value
    assert replay == first
    assert first.status is ToolVersionStatus.PUBLISHED
    second = service.create_version(
        OWNER,
        "admin.alpha",
        PROJECT,
        first.name,
        "Updated description.",
        SCHEMA,
        SCHEMA,
        "WRITE",
        ("replace",),
        "tool-key-2",
        "corr-2",
        tool_id=first.tool_id,
        expected_latest_version=1,
    ).value
    assert second.status is ToolVersionStatus.DRAFT
    assert [item.version for item in service.versions(OWNER, PROJECT, first.tool_id).value] == [
        2,
        1,
    ]


def test_unknown_schema_ambiguous_effect_and_duplicate_actions_are_rejected() -> None:
    service = ToolService(InMemoryToolStore(), Clock())
    unknown = {"$schema": "https://example.invalid/schema", "type": "object"}
    assert (
        service.create_version(
            OWNER, "admin", PROJECT, "tool", "", unknown, SCHEMA, "READ", ("read",), "a", "c"
        ).error.code
        == "tool.invalid_input"
    )
    assert (
        service.create_version(
            OWNER, "admin", PROJECT, "tool", "", SCHEMA, SCHEMA, "MAYBE", ("read",), "b", "c"
        ).error.code
        == "tool.invalid_input"
    )
    assert (
        service.create_version(
            OWNER,
            "admin",
            PROJECT,
            "tool",
            "",
            SCHEMA,
            SCHEMA,
            "READ",
            ("read", "read"),
            "c",
            "c",
        ).error.code
        == "tool.invalid_input"
    )


def test_policy_defaults_safe_and_exact_exception_is_narrow() -> None:
    store = InMemoryPolicyStore()
    service = PolicyService(store, Clock())
    tool_id = uuid4()
    read = service.evaluate(
        OWNER, "admin", PROJECT, tool_id, 2, EffectClass.READ, "search", "documents", "r"
    ).value
    write = service.evaluate(
        OWNER, "admin", PROJECT, tool_id, 2, EffectClass.WRITE, "replace", "doc:1", "w"
    ).value
    assert read.decision == "ALLOW"
    assert write.decision == "REQUIRE_APPROVAL"
    exception = ApprovalException(
        uuid4(), OWNER, PROJECT, tool_id, 2, "replace", "doc:1", NOW + timedelta(hours=1), True
    )
    store.add_exception(exception)
    exact = service.evaluate(
        OWNER, "admin", PROJECT, tool_id, 2, EffectClass.WRITE, "replace", "doc:1", "e"
    ).value
    broader = service.evaluate(
        OWNER, "admin", PROJECT, tool_id, 2, EffectClass.WRITE, "replace", "documents", "b"
    ).value
    timeout = service.evaluate(
        OWNER,
        "admin",
        PROJECT,
        tool_id,
        2,
        EffectClass.WRITE,
        "replace",
        "doc:1",
        "t",
        timed_out=True,
    ).value
    assert exact.decision == "ALLOW" and exact.exception_id == exception.id
    assert broader.decision == "REQUIRE_APPROVAL"
    assert timeout.decision == "DENY" and timeout.exception_id is None
