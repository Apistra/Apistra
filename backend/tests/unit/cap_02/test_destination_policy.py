from __future__ import annotations

import socket

import pytest

from apistra.modules.catalog.adapters import probe as probe_module
from apistra.modules.catalog.adapters.probe import (
    DenyByDefaultDestinationPolicy,
    OpenAiCompatibleEndpointProbe,
)
from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)


def resolved(address: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]


def test_profiles_allow_only_their_explicit_address_class(monkeypatch) -> None:
    policy = DenyByDefaultDestinationPolicy()
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: resolved("127.0.0.1"))
    assert policy.approve("http://localhost:18080/v1", NetworkProfile.LOCAL) is not None
    assert policy.approve("http://localhost:18080/v1", NetworkProfile.CLOUD) is None

    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: resolved("10.0.0.10"))
    assert policy.approve("https://internal.example/v1", NetworkProfile.ON_PREMISE) is not None
    assert policy.approve("https://internal.example/v1", NetworkProfile.CLOUD) is None

    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: resolved("93.184.216.34"))
    assert policy.approve("https://example.com/v1", NetworkProfile.CLOUD) is not None


def test_metadata_and_mixed_dns_answers_are_denied(monkeypatch) -> None:
    policy = DenyByDefaultDestinationPolicy()
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: resolved("169.254.169.254"),
    )
    assert policy.approve("http://metadata.invalid", NetworkProfile.ON_PREMISE) is None

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: resolved("93.184.216.34") + resolved("127.0.0.1"),
    )
    assert policy.approve("https://rebinding.example/v1", NetworkProfile.CLOUD) is None


def test_unresolvable_destination_is_denied(monkeypatch) -> None:
    policy = DenyByDefaultDestinationPolicy()

    def unavailable(*_args, **_kwargs):
        raise OSError("synthetic DNS failure")

    monkeypatch.setattr(socket, "getaddrinfo", unavailable)
    assert policy.approve("https://unavailable.example/v1", NetworkProfile.CLOUD) is None


class FakeResponse:
    def __init__(
        self,
        status: int,
        body: bytes = b'{"data":[{"id":"synthetic-chat"}]}',
    ) -> None:
        self.status = status
        self.body = body
        self.read_size: int | None = None

    def read(self, size: int) -> bytes:
        self.read_size = size
        return self.body


class FakeConnection:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.closed = False

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        self.headers = headers
        assert method == "GET" and path == "/v1/models"
        if isinstance(self.response, Exception):
            raise self.response

    def getresponse(self) -> FakeResponse:
        assert isinstance(self.response, FakeResponse)
        return self.response

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize(
    ("status", "outcome"),
    [
        (200, ProbeOutcome.CONNECTION_VERIFIED),
        (401, ProbeOutcome.AUTHENTICATION_FAILED),
        (302, ProbeOutcome.DESTINATION_BLOCKED),
        (500, ProbeOutcome.CONNECTION_FAILED),
    ],
)
def test_openai_probe_maps_bounded_read_only_responses(monkeypatch, status, outcome) -> None:
    response = FakeResponse(status)
    connection = FakeConnection(response)
    monkeypatch.setattr(
        probe_module.http.client,
        "HTTPConnection",
        lambda *_args, **_kwargs: connection,
    )
    destination = ApprovedDestination("http", "provider.example", 80, "/v1", ("203.0.113.1",))
    result = OpenAiCompatibleEndpointProbe().probe(
        ProviderProtocol.OPENAI_COMPATIBLE,
        destination,
        "synthetic-chat",
        SecretMaterial(b"canary"),
    )
    assert result is outcome
    assert connection.headers["Authorization"] == "Bearer canary"
    assert response.read_size == probe_module.MAXIMUM_PROBE_RESPONSE_BYTES + 1
    assert connection.closed is True


def test_openai_probe_normalizes_timeout_and_unsupported_protocol(monkeypatch) -> None:
    connection = FakeConnection(TimeoutError())
    monkeypatch.setattr(
        probe_module.http.client,
        "HTTPConnection",
        lambda *_args, **_kwargs: connection,
    )
    destination = ApprovedDestination("http", "provider.example", 80, "/v1", ("203.0.113.1",))
    probe = OpenAiCompatibleEndpointProbe()
    assert (
        probe.probe(
            ProviderProtocol.OPENAI_COMPATIBLE,
            destination,
            "synthetic-chat",
            SecretMaterial(b"canary"),
        )
        is ProbeOutcome.TIMED_OUT
    )
    assert (
        probe.probe(
            "UNSUPPORTED",
            destination,
            "synthetic-chat",
            SecretMaterial(b"canary"),
        )
        is ProbeOutcome.PROBE_NOT_SUPPORTED
    )


@pytest.mark.parametrize(
    "body",
    [
        b'{"data":[{"id":"another-model"}]}',
        b"not-json",
        b"x" * (probe_module.MAXIMUM_PROBE_RESPONSE_BYTES + 1),
    ],
)
def test_openai_probe_rejects_missing_malformed_or_oversized_model_catalogue(
    monkeypatch, body
) -> None:
    connection = FakeConnection(FakeResponse(200, body))
    monkeypatch.setattr(
        probe_module.http.client,
        "HTTPConnection",
        lambda *_args, **_kwargs: connection,
    )
    destination = ApprovedDestination("http", "provider.example", 80, "/v1", ("203.0.113.1",))
    assert (
        OpenAiCompatibleEndpointProbe().probe(
            ProviderProtocol.OPENAI_COMPATIBLE,
            destination,
            "synthetic-chat",
            SecretMaterial(b"canary"),
        )
        is ProbeOutcome.CONNECTION_FAILED
    )
