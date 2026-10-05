"""Use cases for immutable, project-scoped agent versions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid4

from apistra.modules.agents.domain import (
    AgentAuditEvent,
    AgentError,
    AgentErrorCode,
    AgentVersion,
    AgentVersionStatus,
    VersionReference,
)
from apistra.modules.agents.ports import AgentClock, AgentStore
from apistra.modules.catalog.public import EndpointPurpose, EndpointService, ToolService
from apistra.modules.policies.public import PolicyService

MAXIMUM_NAME_LENGTH = 128
MAXIMUM_INSTRUCTIONS_LENGTH = 32_768
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
UNAVAILABLE_MESSAGE = "Agent version is unavailable."
type AgentVersionList = list[AgentVersion]
type AgentAuditEventList = list[AgentAuditEvent]


@dataclass(frozen=True, slots=True)
class AgentResult[T]:
    value: T | None = None
    error: AgentError | None = None


class AgentService:
    def __init__(
        self,
        store: AgentStore,
        endpoints: EndpointService,
        tools: ToolService,
        clock: AgentClock,
        policies: PolicyService | None = None,
    ) -> None:
        self._store = store
        self._endpoints = endpoints
        self._tools = tools
        self._clock = clock
        self._policies = policies

    def create_version(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        name: str,
        instructions: str,
        primary_endpoint: VersionReference,
        fallback_endpoint: VersionReference | None,
        tool_versions: tuple[VersionReference, ...],
        limits_policy_version: VersionReference | None,
        idempotency_key: str,
        correlation_id: str,
        *,
        agent_id: UUID | None = None,
        expected_latest_version: int = 0,
    ) -> AgentResult[AgentVersion]:
        normalized_name = name.strip()
        normalized_instructions = instructions.strip()
        validation = self._validate(
            owner_id,
            project_id,
            normalized_name,
            normalized_instructions,
            primary_endpoint,
            fallback_endpoint,
            tool_versions,
            limits_policy_version,
            idempotency_key,
        )
        if validation:
            return AgentResult(error=validation)
        resolved_agent_id = agent_id or uuid4()
        version_number = expected_latest_version + 1
        now = self._clock.now()
        version = AgentVersion(
            agent_id=resolved_agent_id,
            owner_administrator_id=owner_id,
            project_id=project_id,
            version=version_number,
            status=AgentVersionStatus.PUBLISHED
            if version_number == 1
            else AgentVersionStatus.DRAFT,
            name=normalized_name,
            instructions=normalized_instructions,
            primary_endpoint=primary_endpoint,
            fallback_endpoint=fallback_endpoint,
            tool_versions=tool_versions,
            limits_policy_version=limits_policy_version,
            created_at=now,
            created_by=owner_id,
        )
        fingerprint = self._fingerprint(version)
        event = AgentAuditEvent(
            id=uuid4(),
            event_type="agent.version_created",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=owner_id,
            actor_username=actor_username,
            project_id=project_id,
            agent_id=resolved_agent_id,
            agent_version=version_number,
            details={"status": version.status},
        )
        stored, conflict = self._store.create_version(
            version, event, idempotency_key, fingerprint, expected_latest_version
        )
        return (
            AgentResult(value=stored) if stored else AgentResult(error=self._store_error(conflict))
        )

    def list(self, owner_id: UUID, project_id: UUID) -> AgentResult[AgentVersionList]:
        return AgentResult(value=self._store.list_latest_for_project(owner_id, project_id))

    def versions(
        self, owner_id: UUID, project_id: UUID, agent_id: UUID
    ) -> AgentResult[AgentVersionList]:
        versions = self._store.list_versions(owner_id, project_id, agent_id)
        return AgentResult(value=versions) if versions else AgentResult(error=self._unavailable())

    def audit_events(self, owner_id: UUID) -> AgentResult[AgentAuditEventList]:
        return AgentResult(value=self._store.list_audit_for_owner(owner_id))

    def _validate(
        self,
        owner_id: UUID,
        project_id: UUID,
        name: str,
        instructions: str,
        primary: VersionReference,
        fallback: VersionReference | None,
        tools: tuple[VersionReference, ...],
        limits_policy: VersionReference | None,
        idempotency_key: str,
    ) -> AgentError | None:
        if not 1 <= len(name) <= MAXIMUM_NAME_LENGTH:
            return self._invalid("Agent name must contain 1 to 128 characters.")
        if not 1 <= len(instructions) <= MAXIMUM_INSTRUCTIONS_LENGTH:
            return self._invalid(
                "Instructions are required and may contain at most 32768 characters."
            )
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return self._invalid("Idempotency-Key must contain 1 to 128 characters.")
        if fallback == primary:
            return self._invalid("Primary and fallback endpoints must be different.")
        for reference in (primary, fallback):
            if reference and not self._endpoints.exact_reference_available(
                owner_id, project_id, reference.id, reference.version, EndpointPurpose.GENERATIVE
            ):
                return self._invalid(
                    "Endpoint reference must identify an exact generative endpoint "
                    "version in the same project."
                )
        if len(set(tools)) != len(tools):
            return self._invalid("Tool version references must be unique.")
        if any(
            not self._tools.exact_reference_available(
                owner_id, project_id, reference.id, reference.version
            )
            for reference in tools
        ):
            return self._invalid(
                "Tool reference must identify an exact tool version in the same project."
            )
        if limits_policy and (
            self._policies is None
            or not self._policies.exact_limit_policy_available(
                owner_id, project_id, limits_policy.id, limits_policy.version
            )
        ):
            return self._invalid(
                "Limits policy reference must identify an exact policy version in the same project."
            )
        return None

    @staticmethod
    def _fingerprint(version: AgentVersion) -> str:
        values = (
            str(version.version),
            version.name,
            version.instructions,
            f"{version.primary_endpoint.id}@{version.primary_endpoint.version}",
            f"{version.fallback_endpoint.id}@{version.fallback_endpoint.version}"
            if version.fallback_endpoint
            else "",
            *(f"{item.id}@{item.version}" for item in version.tool_versions),
            f"{version.limits_policy_version.id}@{version.limits_policy_version.version}"
            if version.limits_policy_version
            else "",
        )
        return hashlib.sha256("\0".join(values).encode()).hexdigest()

    @staticmethod
    def _invalid(message: str) -> AgentError:
        return AgentError(AgentErrorCode.INVALID_INPUT, message)

    @staticmethod
    def _unavailable() -> AgentError:
        return AgentError(AgentErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE)

    @staticmethod
    def _store_error(conflict: str | None) -> AgentError:
        if conflict == "version":
            return AgentError(
                AgentErrorCode.VERSION_CONFLICT, "The agent has changed. Reload it and try again."
            )
        if conflict == "idempotency":
            return AgentError(
                AgentErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        return AgentService._unavailable()
