"""Ports for endpoint persistence and credential-safe connection probes."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    EndpointAuditEvent,
    ModelEndpoint,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)


class EndpointStore(Protocol):
    def create(
        self,
        endpoint: ModelEndpoint,
        event: EndpointAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> tuple[ModelEndpoint | None, str | None]: ...

    def list_for_project(self, owner_id: UUID, project_id: UUID) -> list[ModelEndpoint]: ...

    def get_for_project(
        self, owner_id: UUID, project_id: UUID, endpoint_id: UUID
    ) -> ModelEndpoint | None: ...

    def record_probe(
        self,
        owner_id: UUID,
        project_id: UUID,
        endpoint_id: UUID,
        expected_version: int,
        outcome: ProbeOutcome,
        updated_at: datetime,
        event: EndpointAuditEvent,
    ) -> tuple[ModelEndpoint | None, str | None]: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[EndpointAuditEvent]: ...


class DestinationPolicy(Protocol):
    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None: ...


class EndpointProbe(Protocol):
    def probe(
        self,
        protocol: ProviderProtocol | str,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome: ...
