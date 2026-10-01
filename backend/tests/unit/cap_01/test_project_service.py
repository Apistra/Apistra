from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.domain import ProjectErrorCode, ProjectStatus


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 1, 14, tzinfo=UTC)


def service() -> tuple[ProjectService, InMemoryProjectStore]:
    store = InMemoryProjectStore()
    return ProjectService(store, Clock()), store


def create_project(projects: ProjectService, owner: UUID, key: str = "ATLAS"):
    return projects.create(
        owner, "admin.alpha", "Atlas Research", key, f"idem-{key}", "corr-create"
    )


def test_create_replay_update_archive_and_audit() -> None:
    projects, store = service()
    owner = uuid4()
    created = create_project(projects, owner)
    replay = create_project(projects, owner)
    assert created.succeeded and replay.value.id == created.value.id
    assert len(store.audit_events) == 1
    assert store.audit_events[0].event_type == "project.created"

    updated = projects.update(
        owner,
        "admin.alpha",
        created.value.id,
        1,
        "Atlas Platform",
        "atlas-2",
        "corr-update",
    )
    assert updated.value.key == "ATLAS-2"
    assert updated.value.version == 2
    archived = projects.archive(owner, "admin.alpha", created.value.id, 2, "corr-archive")
    assert archived.value.status is ProjectStatus.ARCHIVED
    assert archived.value.version == 3
    assert [event.event_type for event in store.audit_events] == [
        "project.created",
        "project.updated",
        "project.archived",
    ]


def test_owner_key_version_and_idempotency_conflicts_change_no_state() -> None:
    projects, store = service()
    owner = uuid4()
    foreign_owner = uuid4()
    created = create_project(projects, owner)

    foreign = projects.get(foreign_owner, created.value.id)
    unknown = projects.get(owner, uuid4())
    assert foreign.error == unknown.error
    assert foreign.error.code is ProjectErrorCode.NOT_FOUND

    stale = projects.update(owner, "admin.alpha", created.value.id, 7, "Changed", "CHANGED", "corr")
    assert stale.error.code is ProjectErrorCode.VERSION_CONFLICT
    assert projects.get(owner, created.value.id).value.name == "Atlas Research"

    replay_conflict = projects.create(
        owner, "admin.alpha", "Different", "DIFFERENT", "idem-ATLAS", "corr"
    )
    assert replay_conflict.error.code is ProjectErrorCode.IDEMPOTENCY_CONFLICT
    assert len(store.audit_events) == 1


def test_validation_and_key_uniqueness_are_owner_scoped() -> None:
    projects, _store = service()
    first_owner = uuid4()
    second_owner = uuid4()
    assert create_project(projects, first_owner).succeeded
    duplicate = projects.create(first_owner, "admin.alpha", "Other", "ATLAS", "idem-other", "corr")
    assert duplicate.error.code is ProjectErrorCode.KEY_CONFLICT
    assert create_project(projects, second_owner).succeeded
    invalid = projects.create(first_owner, "admin.alpha", "", "not valid", "idem-invalid", "corr")
    assert invalid.error.code is ProjectErrorCode.INVALID_INPUT


def test_concurrent_idempotent_delivery_creates_one_project_and_event() -> None:
    projects, store = service()
    owner = uuid4()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _index: create_project(projects, owner), range(16)))
    assert len({result.value.id for result in results}) == 1
    assert len(projects.list(owner).value) == 1
    assert [event.event_type for event in store.audit_events] == ["project.created"]


def test_audit_events_are_filtered_by_authenticated_owner() -> None:
    projects, _store = service()
    owner = uuid4()
    foreign_owner = uuid4()
    owned = create_project(projects, owner, "OWNED").value
    foreign = create_project(projects, foreign_owner, "SECRET").value

    events = projects.audit_events(owner).value

    assert [(event.event_type, event.project_id, event.project_key) for event in events] == [
        ("project.created", owned.id, "OWNED")
    ]
    assert foreign.id not in {event.project_id for event in events}
    assert "SECRET" not in repr(events)
