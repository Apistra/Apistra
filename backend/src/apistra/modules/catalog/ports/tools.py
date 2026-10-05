"""Persistence boundary for immutable governed tool versions."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from apistra.modules.catalog.domain.tools import ToolAuditEvent, ToolVersion


class ToolStore(Protocol):
    def create_version(
        self,
        version: ToolVersion,
        event: ToolAuditEvent,
        idempotency_key: str,
        request_fingerprint: str,
        expected_latest_version: int,
    ) -> tuple[ToolVersion | None, str | None]: ...

    def list_latest_for_project(self, owner_id: UUID, project_id: UUID) -> list[ToolVersion]: ...

    def list_versions(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID
    ) -> list[ToolVersion]: ...

    def get_exact(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID, version: int
    ) -> ToolVersion | None: ...

    def list_audit_for_owner(self, owner_id: UUID) -> list[ToolAuditEvent]: ...


class ToolClock(Protocol):
    def now(self) -> datetime: ...
