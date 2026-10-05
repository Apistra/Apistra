"""Use cases for immutable, project-scoped governed tool contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from apistra.modules.catalog.domain.tools import (
    ToolAuditEvent,
    ToolError,
    ToolErrorCode,
    ToolVersion,
    ToolVersionStatus,
)
from apistra.modules.catalog.ports.tools import ToolClock, ToolStore

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
MAXIMUM_NAME_LENGTH = 128
MAXIMUM_DESCRIPTION_LENGTH = 4096
MAXIMUM_ACTIONS = 128
MAXIMUM_ACTION_LENGTH = 128
MAXIMUM_IDEMPOTENCY_KEY_LENGTH = 128
UNAVAILABLE_MESSAGE = "Tool version is unavailable."
type ToolVersionList = list[ToolVersion]
type ToolAuditEventList = list[ToolAuditEvent]


@dataclass(frozen=True, slots=True)
class ToolResult[T]:
    value: T | None = None
    error: ToolError | None = None


class ToolService:
    def __init__(self, store: ToolStore, clock: ToolClock) -> None:
        self._store = store
        self._clock = clock

    def create_version(
        self,
        owner_id: UUID,
        actor_username: str,
        project_id: UUID,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        effect_class: str,
        actions: tuple[str, ...],
        idempotency_key: str,
        correlation_id: str,
        *,
        tool_id: UUID | None = None,
        expected_latest_version: int = 0,
    ) -> ToolResult[ToolVersion]:
        normalized_name = name.strip()
        normalized_description = description.strip()
        normalized_actions = tuple(action.strip() for action in actions)
        validation = self._validate(
            normalized_name,
            normalized_description,
            input_schema,
            output_schema,
            effect_class,
            normalized_actions,
            idempotency_key,
        )
        if validation:
            return ToolResult(error=validation)
        resolved_tool_id = tool_id or uuid4()
        version_number = expected_latest_version + 1
        now = self._clock.now()
        version = ToolVersion(
            tool_id=resolved_tool_id,
            owner_administrator_id=owner_id,
            project_id=project_id,
            version=version_number,
            status=(
                ToolVersionStatus.PUBLISHED if version_number == 1 else ToolVersionStatus.DRAFT
            ),
            name=normalized_name,
            description=normalized_description,
            input_schema=input_schema,
            output_schema=output_schema,
            effect_class=effect_class,
            actions=normalized_actions,
            created_at=now,
            created_by=owner_id,
        )
        event = ToolAuditEvent(
            id=uuid4(),
            event_type="tool.version_created",
            created_at=now,
            correlation_id=correlation_id,
            actor_id=owner_id,
            actor_username=actor_username,
            project_id=project_id,
            tool_id=resolved_tool_id,
            tool_version=version_number,
            details={"status": version.status, "effect_class": effect_class},
        )
        stored, conflict = self._store.create_version(
            version,
            event,
            idempotency_key,
            self._fingerprint(version),
            expected_latest_version,
        )
        return ToolResult(value=stored) if stored else ToolResult(error=self._store_error(conflict))

    def list(self, owner_id: UUID, project_id: UUID) -> ToolResult[ToolVersionList]:
        return ToolResult(value=self._store.list_latest_for_project(owner_id, project_id))

    def versions(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID
    ) -> ToolResult[ToolVersionList]:
        values = self._store.list_versions(owner_id, project_id, tool_id)
        return ToolResult(value=values) if values else ToolResult(error=self._unavailable())

    def exact(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID, version: int
    ) -> ToolResult[ToolVersion]:
        value = self._store.get_exact(owner_id, project_id, tool_id, version)
        return ToolResult(value=value) if value else ToolResult(error=self._unavailable())

    def exact_reference_available(
        self, owner_id: UUID, project_id: UUID, tool_id: UUID, version: int
    ) -> bool:
        return self._store.get_exact(owner_id, project_id, tool_id, version) is not None

    def audit_events(self, owner_id: UUID) -> ToolResult[ToolAuditEventList]:
        return ToolResult(value=self._store.list_audit_for_owner(owner_id))

    @staticmethod
    def _validate(
        name: str,
        description: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        effect_class: str,
        actions: tuple[str, ...],
        idempotency_key: str,
    ) -> ToolError | None:
        if not 1 <= len(name) <= MAXIMUM_NAME_LENGTH:
            return ToolService._invalid("Tool name must contain 1 to 128 characters.")
        if len(description) > MAXIMUM_DESCRIPTION_LENGTH:
            return ToolService._invalid("Tool description may contain at most 4096 characters.")
        if effect_class not in {"READ", "WRITE", "ADMINISTRATIVE"}:
            return ToolService._invalid("Effect class must be explicit and supported.")
        if not 1 <= len(actions) <= MAXIMUM_ACTIONS or len(set(actions)) != len(actions):
            return ToolService._invalid("Actions must be a non-empty unique list.")
        if any(not action or len(action) > MAXIMUM_ACTION_LENGTH for action in actions):
            return ToolService._invalid("Each action must contain 1 to 128 characters.")
        if not ToolService._supported_schema(input_schema):
            return ToolService._invalid("Input schema must use JSON Schema draft 2020-12.")
        if not ToolService._supported_schema(output_schema):
            return ToolService._invalid("Output schema must use JSON Schema draft 2020-12.")
        if not 1 <= len(idempotency_key) <= MAXIMUM_IDEMPOTENCY_KEY_LENGTH:
            return ToolService._invalid("Idempotency-Key must contain 1 to 128 characters.")
        return None

    @staticmethod
    def _supported_schema(schema: dict[str, Any]) -> bool:
        return schema.get("$schema") == JSON_SCHEMA_DIALECT and schema.get("type") == "object"

    @staticmethod
    def _fingerprint(version: ToolVersion) -> str:
        payload = {
            "version": version.version,
            "name": version.name,
            "description": version.description,
            "input_schema": version.input_schema,
            "output_schema": version.output_schema,
            "effect_class": version.effect_class,
            "actions": version.actions,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _invalid(message: str) -> ToolError:
        return ToolError(ToolErrorCode.INVALID_INPUT, message)

    @staticmethod
    def _unavailable() -> ToolError:
        return ToolError(ToolErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE)

    @staticmethod
    def _store_error(conflict: str | None) -> ToolError:
        if conflict == "version":
            return ToolError(
                ToolErrorCode.VERSION_CONFLICT, "The tool has changed. Reload it and try again."
            )
        if conflict == "idempotency":
            return ToolError(
                ToolErrorCode.IDEMPOTENCY_CONFLICT,
                "Idempotency-Key was already used for a different request.",
            )
        return ToolService._unavailable()
