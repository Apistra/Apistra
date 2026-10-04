"""Endpoint catalogue use cases with an explicit credential-release boundary."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.domain.endpoints import (
    EndpointAuditEvent,
    EndpointError,
    EndpointErrorCode,
    EndpointPurpose,
    EndpointStatus,
    ModelEndpoint,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)
from apistra.modules.catalog.ports import SecretClock
from apistra.modules.catalog.ports.endpoints import DestinationPolicy, EndpointProbe, EndpointStore

ENDPOINT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
MAXIMUM_MODEL_IDENTIFIER_LENGTH = 256
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
UNAVAILABLE_MESSAGE = "Endpoint is unavailable."
type EndpointList = list[ModelEndpoint]
type EndpointAuditEventList = list[EndpointAuditEvent]


@dataclass(frozen=True, slots=True)
class EndpointResult[T]:
    value: T | None = None
    error: EndpointError | None = None


class EndpointService:
    def __init__(
        self,
        store: EndpointStore,
        secrets: SecretService,
        destination_policy: DestinationPolicy,
        probe: EndpointProbe,
        clock: SecretClock,
    ) -> None:
        self._store = store
        self._secrets = secrets
        self._destination_policy = destination_policy
        self._probe = probe
        self._clock = clock

    def create(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        name: str,
        purpose: EndpointPurpose,
        provider_protocol: ProviderProtocol,
        base_url: str,
        model_identifier: str,
        secret_reference_id: UUID,
        network_profile: NetworkProfile,
        idempotency_key: str,
        correlation_id: str,
    ) -> EndpointResult[ModelEndpoint]:
        normalized_name = name.strip().lower()
        normalized_url = base_url.strip().rstrip("/")
        normalized_model = model_identifier.strip()
        validation = self._validate(normalized_name, normalized_url, normalized_model)
        if validation:
            return EndpointResult(error=validation)
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return self._invalid("Idempotency-Key must contain 1 to 128 characters.")
        if not self._secrets.reference_available(owner_id, project_id, secret_reference_id):
            return self._invalid("Secret reference must be active in the same project.")
        now = self._clock.now()
        endpoint = ModelEndpoint(
            id=uuid4(),
            owner_administrator_id=owner_id,
            project_id=project_id,
            name=normalized_name,
            purpose=purpose,
            provider_protocol=provider_protocol,
            base_url=normalized_url,
            model_identifier=normalized_model,
            secret_reference_id=secret_reference_id,
            network_profile=network_profile,
            status=EndpointStatus.UNVERIFIED,
            version=1,
            last_probe_outcome=None,
            created_at=now,
            updated_at=now,
        )
        event = self._event("endpoint.created", endpoint, actor_username, correlation_id)
        fingerprint = hashlib.sha256(
            "\0".join(
                (
                    normalized_name,
                    purpose,
                    provider_protocol,
                    normalized_url,
                    normalized_model,
                    str(secret_reference_id),
                    network_profile,
                )
            ).encode()
        ).hexdigest()
        stored, conflict = self._store.create(endpoint, event, idempotency_key, fingerprint)
        return (
            EndpointResult(value=stored)
            if stored
            else EndpointResult(error=self._store_error(conflict))
        )

    def list(self, owner_id: UUID, project_id: UUID) -> EndpointResult[EndpointList]:
        return EndpointResult(value=self._store.list_for_project(owner_id, project_id))

    def test_connection(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        endpoint_id: UUID,
        expected_version: int,
        correlation_id: str,
    ) -> EndpointResult[ModelEndpoint]:
        current = self._store.get_for_project(owner_id, project_id, endpoint_id)
        if current is None:
            return self._unavailable()
        if current.version != expected_version:
            return EndpointResult(error=self._store_error("version"))
        destination = self._destination_policy.approve(current.base_url, current.network_profile)
        if destination is None:
            outcome = ProbeOutcome.DESTINATION_BLOCKED
        else:
            material = self._secrets.resolve(owner_id, project_id, current.secret_reference_id)
            if material.value is None:
                return self._unavailable()
            outcome = self._probe.probe(
                current.provider_protocol,
                destination,
                current.model_identifier,
                material.value,
            )
        event = self._event(
            "endpoint.connection_tested",
            current,
            actor_username,
            correlation_id,
            {"outcome": outcome},
        )
        stored, conflict = self._store.record_probe(
            owner_id,
            project_id,
            endpoint_id,
            expected_version,
            outcome,
            self._clock.now(),
            event,
        )
        return (
            EndpointResult(value=stored)
            if stored
            else EndpointResult(error=self._store_error(conflict))
        )

    def audit_events(self, owner_id: UUID) -> EndpointResult[EndpointAuditEventList]:
        return EndpointResult(value=self._store.list_audit_for_owner(owner_id))

    @staticmethod
    def _validate(name: str, base_url: str, model_identifier: str) -> EndpointError | None:
        if not ENDPOINT_NAME_PATTERN.fullmatch(name):
            return EndpointError(
                EndpointErrorCode.INVALID_INPUT,
                "Endpoint name must contain 2 to 64 lowercase letters, numbers, "
                "dots, dashes, or underscores.",
            )
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return EndpointError(
                EndpointErrorCode.INVALID_INPUT, "Base URL must be an absolute HTTP or HTTPS URL."
            )
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            return EndpointError(
                EndpointErrorCode.INVALID_INPUT,
                "Base URL must not contain credentials, a query, or a fragment.",
            )
        if not 1 <= len(model_identifier) <= MAXIMUM_MODEL_IDENTIFIER_LENGTH:
            return EndpointError(
                EndpointErrorCode.INVALID_INPUT,
                "Model identifier is required and may contain at most 256 characters.",
            )
        return None

    @staticmethod
    def _event(
        event_type: str,
        endpoint: ModelEndpoint,
        actor_username: str,
        correlation_id: str,
        details: dict[str, object] | None = None,
    ) -> EndpointAuditEvent:
        return EndpointAuditEvent(
            id=uuid4(),
            event_type=event_type,
            created_at=endpoint.updated_at,
            correlation_id=correlation_id,
            actor_id=endpoint.owner_administrator_id,
            actor_username=actor_username,
            project_id=endpoint.project_id,
            endpoint_id=endpoint.id,
            details=details or {},
        )

    @staticmethod
    def _invalid(message: str) -> EndpointResult[ModelEndpoint]:
        return EndpointResult(error=EndpointError(EndpointErrorCode.INVALID_INPUT, message))

    @staticmethod
    def _unavailable[T]() -> EndpointResult[T]:
        return EndpointResult(
            error=EndpointError(EndpointErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE)
        )

    @staticmethod
    def _store_error(conflict: str | None) -> EndpointError:
        if conflict == "name":
            return EndpointError(
                EndpointErrorCode.NAME_CONFLICT, "Endpoint name is already in use."
            )
        if conflict == "version":
            return EndpointError(
                EndpointErrorCode.VERSION_CONFLICT,
                "The endpoint has changed. Reload it and try again.",
            )
        if conflict == "idempotency":
            return EndpointError(
                EndpointErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        return EndpointError(EndpointErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE)
