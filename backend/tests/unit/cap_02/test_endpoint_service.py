from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_memory import InMemoryEndpointStore
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    EndpointPurpose,
    EndpointStatus,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)

OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")
PROJECT_ID = UUID("00000000-0000-0000-0000-000000000002")
CANARY = "CAP02-ENDPOINT-CANARY"


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 4, 18, tzinfo=UTC)


class Policy:
    def __init__(self, destination: ApprovedDestination | None) -> None:
        self.destination = destination
        self.calls = 0

    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None:
        self.calls += 1
        return self.destination


class Probe:
    def __init__(self, outcome: ProbeOutcome) -> None:
        self.outcome = outcome
        self.calls = 0

    def probe(
        self,
        protocol: ProviderProtocol,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome:
        self.calls += 1
        assert credential.value.decode() == CANARY
        return self.outcome


def services(
    destination: ApprovedDestination | None,
    outcome: ProbeOutcome = ProbeOutcome.CONNECTION_VERIFIED,
) -> tuple[EndpointService, SecretService, Policy, Probe, UUID]:
    secrets = SecretService(
        InMemorySecretStore(),
        AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))}),
        Clock(),
        "installation-test",
    )
    reference = secrets.create(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        "provider-primary",
        "Endpoint credential",
        CANARY,
        "create-secret",
        "correlation-secret",
    ).value
    assert reference is not None
    policy = Policy(destination)
    probe = Probe(outcome)
    endpoints = EndpointService(InMemoryEndpointStore(), secrets, policy, probe, Clock())
    return endpoints, secrets, policy, probe, reference.id


def create_endpoint(service: EndpointService, reference_id: UUID):
    result = service.create(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        "local-llm",
        EndpointPurpose.GENERATIVE,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "http://127.0.0.1:18080/v1/",
        "synthetic-chat",
        reference_id,
        NetworkProfile.LOCAL,
        "create-local-llm",
        "correlation-create",
    )
    assert result.value is not None
    return result.value


def test_create_is_offline_idempotent_and_unverified() -> None:
    endpoints, _secrets, policy, probe, reference_id = services(None)
    created = create_endpoint(endpoints, reference_id)
    replay = create_endpoint(endpoints, reference_id)
    assert replay.id == created.id
    assert created.status is EndpointStatus.UNVERIFIED
    assert created.base_url == "http://127.0.0.1:18080/v1"
    assert policy.calls == probe.calls == 0


def test_blocked_destination_never_resolves_secret_or_calls_probe() -> None:
    endpoints, secrets, policy, probe, reference_id = services(None)
    created = create_endpoint(endpoints, reference_id)
    original_resolve = secrets.resolve

    def forbidden_resolve(owner_id: UUID, project_id: UUID, requested_id: UUID):
        raise AssertionError("credential resolution must happen after destination approval")

    secrets.resolve = forbidden_resolve  # type: ignore[method-assign]
    result = endpoints.test_connection(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        created.id,
        1,
        "correlation-probe",
    )
    secrets.resolve = original_resolve  # type: ignore[method-assign]
    assert result.value is not None
    assert result.value.last_probe_outcome is ProbeOutcome.DESTINATION_BLOCKED
    assert result.value.status is EndpointStatus.UNVERIFIED
    assert policy.calls == 1 and probe.calls == 0


def test_approved_destination_resolves_once_and_records_verified_result() -> None:
    destination = ApprovedDestination("http", "127.0.0.1", 18080, "/v1", ("127.0.0.1",))
    endpoints, _secrets, policy, probe, reference_id = services(destination)
    created = create_endpoint(endpoints, reference_id)
    result = endpoints.test_connection(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        created.id,
        1,
        "correlation-probe",
    )
    assert result.value is not None
    assert result.value.status is EndpointStatus.VERIFIED
    assert result.value.last_probe_outcome is ProbeOutcome.CONNECTION_VERIFIED
    assert result.value.version == 2
    assert policy.calls == probe.calls == 1


def test_stale_probe_is_rejected_before_policy_secret_or_network_access() -> None:
    destination = ApprovedDestination("http", "127.0.0.1", 18080, "/v1", ("127.0.0.1",))
    endpoints, secrets, policy, probe, reference_id = services(destination)
    created = create_endpoint(endpoints, reference_id)
    original_resolve = secrets.resolve

    def forbidden_resolve(owner_id: UUID, project_id: UUID, requested_id: UUID):
        raise AssertionError("stale probe must not resolve credentials")

    secrets.resolve = forbidden_resolve  # type: ignore[method-assign]
    result = endpoints.test_connection(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        created.id,
        9,
        "correlation-stale",
    )
    secrets.resolve = original_resolve  # type: ignore[method-assign]
    assert result.error is not None
    assert result.error.code == "endpoint.version_conflict"
    assert policy.calls == probe.calls == 0


def test_invalid_url_and_foreign_secret_are_rejected_without_network() -> None:
    endpoints, _secrets, policy, probe, reference_id = services(None)
    invalid = endpoints.create(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        "local-llm",
        EndpointPurpose.GENERATIVE,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "file:///tmp/model",
        "synthetic-chat",
        reference_id,
        NetworkProfile.LOCAL,
        "invalid-url",
        "correlation-invalid",
    )
    foreign = endpoints.create(
        OWNER_ID,
        "admin.alpha",
        PROJECT_ID,
        "foreign-secret",
        EndpointPurpose.EMBEDDING,
        ProviderProtocol.OPENAI_COMPATIBLE,
        "https://example.com/v1",
        "embedding-model",
        uuid4(),
        NetworkProfile.CLOUD,
        "foreign-secret",
        "correlation-invalid",
    )
    assert invalid.error is not None and foreign.error is not None
    assert policy.calls == probe.calls == 0
