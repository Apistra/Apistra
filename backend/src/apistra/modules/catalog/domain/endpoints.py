"""Provider-neutral endpoint catalogue domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class EndpointPurpose(StrEnum):
    GENERATIVE = "GENERATIVE"
    EMBEDDING = "EMBEDDING"


class ProviderProtocol(StrEnum):
    OPENAI_COMPATIBLE = "OPENAI_COMPATIBLE"


class NetworkProfile(StrEnum):
    CLOUD = "CLOUD"
    ON_PREMISE = "ON_PREMISE"
    LOCAL = "LOCAL"


class EndpointStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class ProbeOutcome(StrEnum):
    CONNECTION_VERIFIED = "CONNECTION_VERIFIED"
    CONNECTION_FAILED = "CONNECTION_FAILED"
    DESTINATION_BLOCKED = "DESTINATION_BLOCKED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TIMED_OUT = "TIMED_OUT"
    PROBE_NOT_SUPPORTED = "PROBE_NOT_SUPPORTED"


class EndpointErrorCode(StrEnum):
    INVALID_INPUT = "endpoint.invalid_input"
    UNAVAILABLE = "endpoint.unavailable"
    NAME_CONFLICT = "endpoint.name_conflict"
    VERSION_CONFLICT = "endpoint.version_conflict"
    IDEMPOTENCY_CONFLICT = "endpoint.idempotency_conflict"


@dataclass(frozen=True, slots=True)
class EndpointError:
    code: EndpointErrorCode
    message: str


@dataclass(frozen=True, slots=True)
class ModelEndpoint:
    id: UUID
    owner_administrator_id: UUID
    project_id: UUID
    name: str
    purpose: EndpointPurpose
    provider_protocol: ProviderProtocol
    base_url: str
    model_identifier: str
    secret_reference_id: UUID
    network_profile: NetworkProfile
    status: EndpointStatus
    version: int
    last_probe_outcome: ProbeOutcome | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EndpointAuditEvent:
    id: UUID
    event_type: str
    created_at: datetime
    correlation_id: str
    actor_id: UUID
    actor_username: str
    project_id: UUID
    endpoint_id: UUID
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApprovedDestination:
    scheme: str
    host: str
    port: int
    base_path: str
    addresses: tuple[str, ...]
