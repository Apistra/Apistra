"""HTTP boundary for project-scoped immutable agent versions."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.modules.agents.application import AgentService
from apistra.modules.agents.domain import AgentError, AgentErrorCode, AgentVersion, VersionReference
from apistra.modules.identity.domain import SessionContext
from apistra.modules.projects.application import ProjectService

SESSION_COOKIE = "apistra_session"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
PROBLEM_MEDIA_TYPE = "application/problem+json"
AGENT_TAG = "agents"
MAXIMUM_AGENT_NAME_LENGTH = 128
MAXIMUM_AGENT_INSTRUCTIONS_LENGTH = 32_768
MAXIMUM_AGENT_TOOL_REFERENCES = 128
UNAVAILABLE_MESSAGE = "Agent version is unavailable."
type Authenticate = Callable[[Request, str | None, str | None, bool], SessionContext | JSONResponse]


class VersionReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    version: int = Field(ge=1)


class AgentVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=MAXIMUM_AGENT_NAME_LENGTH)
    instructions: str = Field(min_length=1, max_length=MAXIMUM_AGENT_INSTRUCTIONS_LENGTH)
    primary_endpoint: VersionReferenceRequest
    fallback_endpoint: VersionReferenceRequest | None = None
    tool_versions: list[VersionReferenceRequest] = Field(
        default_factory=list, max_length=MAXIMUM_AGENT_TOOL_REFERENCES
    )
    limits_policy_version: VersionReferenceRequest | None = None


def _problem(error: AgentError, correlation_id: str) -> JSONResponse:
    codes = {
        AgentErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        AgentErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        AgentErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        AgentErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
    }
    return JSONResponse(
        status_code=codes[error.code],
        content={
            "type": f"https://apistra.dev/problems/{error.code}",
            "title": error.code,
            "detail": error.message,
            "correlation_id": correlation_id,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _reference(reference: VersionReference | None) -> dict[str, object] | None:
    return {"id": str(reference.id), "version": reference.version} if reference else None


def _version(version: AgentVersion) -> dict[str, object]:
    return {
        "agent_id": str(version.agent_id),
        "project_id": str(version.project_id),
        "version": version.version,
        "status": version.status,
        "name": version.name,
        "instructions": version.instructions,
        "primary_endpoint": _reference(version.primary_endpoint),
        "fallback_endpoint": _reference(version.fallback_endpoint),
        "tool_versions": [_reference(item) for item in version.tool_versions],
        "limits_policy_version": _reference(version.limits_policy_version),
        "created_at": version.created_at.isoformat(),
        "created_by": str(version.created_by),
    }


def _to_reference(value: VersionReferenceRequest | None) -> VersionReference | None:
    return VersionReference(value.id, value.version) if value else None


def _required_reference(value: VersionReferenceRequest) -> VersionReference:
    return VersionReference(value.id, value.version)


def _references(values: list[VersionReferenceRequest]) -> tuple[VersionReference, ...]:
    return tuple(_required_reference(item) for item in values)


def register_agent_routes(  # noqa: C901 - route declarations are deliberately colocated
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    agents: AgentService,
) -> None:
    @application.get("/api/v1/projects/{project_id}/agents", tags=[AGENT_TAG], response_model=None)
    def list_agents(
        project_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        if projects.get(context.session.administrator_id, project_id).error:
            return _problem(
                AgentError(AgentErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        return {
            "items": [
                _version(item)
                for item in agents.list(context.session.administrator_id, project_id).value or []
            ]
        }

    @application.post(
        "/api/v1/projects/{project_id}/agents",
        tags=[AGENT_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_agent(
        project_id: UUID,
        payload: AgentVersionRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        if projects.get(context.session.administrator_id, project_id).error:
            return _problem(
                AgentError(AgentErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        result = agents.create_version(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.instructions,
            _required_reference(payload.primary_endpoint),
            _to_reference(payload.fallback_endpoint),
            _references(payload.tool_versions),
            _to_reference(payload.limits_policy_version),
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or AgentError(AgentErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _version(result.value)

    @application.post(
        "/api/v1/projects/{project_id}/agents/{agent_id}/versions",
        tags=[AGENT_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_agent_version(
        project_id: UUID,
        agent_id: UUID,
        payload: AgentVersionRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
        if_match: str | None = Header(None, alias="if-match"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        expected = int(if_match.strip('"')) if if_match and if_match.strip('"').isdigit() else 0
        result = agents.create_version(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.instructions,
            _required_reference(payload.primary_endpoint),
            _to_reference(payload.fallback_endpoint),
            _references(payload.tool_versions),
            _to_reference(payload.limits_policy_version),
            idempotency_key or "",
            request.state.correlation_id,
            agent_id=agent_id,
            expected_latest_version=expected,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or AgentError(AgentErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _version(result.value)

    @application.get(
        "/api/v1/projects/{project_id}/agents/{agent_id}/versions",
        tags=[AGENT_TAG],
        response_model=None,
    )
    def list_agent_versions(
        project_id: UUID,
        agent_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        result = agents.versions(context.session.administrator_id, project_id, agent_id)
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        return {"items": [_version(item) for item in result.value or []]}
