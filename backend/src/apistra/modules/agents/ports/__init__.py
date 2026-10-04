"""Persistence boundary for versioned agents."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.agents.domain import AgentAuditEvent, AgentVersion


class AgentStore(Protocol):
    def create_version(
        self,
        version: AgentVersion,
        event: AgentAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[AgentVersion | None, str | None]: ...

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[AgentVersion]: ...

    def list_versions(
        self, owner_id: UUID, project_id: UUID, agent_id: UUID
    ) -> list[AgentVersion]: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[AgentAuditEvent]: ...


class AgentClock(Protocol):
    def now(self) -> datetime: ...
