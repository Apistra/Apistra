"""HTTP boundary for governed tool contracts and approval classification."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.modules.catalog.public import (
    ToolError,
    ToolErrorCode,
    ToolService,
    ToolVersion,
)
from apistra.modules.identity.domain import SessionContext
from apistra.modules.policies.public import (
    EffectClass,
    PolicyError,
    PolicyErrorCode,
    PolicyService,
)
from apistra.modules.projects.application import ProjectService

SESSION_COOKIE = "apistra_session"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
PROBLEM_MEDIA_TYPE = "application/problem+json"
TOOLS_TAG = "tools"
MAXIMUM_TOOL_NAME_LENGTH = 128
MAXIMUM_TOOL_DESCRIPTION_LENGTH = 4096
MAXIMUM_TOOL_ACTIONS = 128
MAXIMUM_TOOL_ACTION_LENGTH = 128
MAXIMUM_POLICY_SCOPE_LENGTH = 512
UNAVAILABLE_MESSAGE = "Tool version is unavailable."
type Authenticate = Callable[[Request, str | None, str | None, bool], SessionContext | JSONResponse]


class ToolVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=MAXIMUM_TOOL_NAME_LENGTH)
    description: str = Field(default="", max_length=MAXIMUM_TOOL_DESCRIPTION_LENGTH)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    effect_class: EffectClass
    actions: list[str] = Field(
        min_length=1,
        max_length=MAXIMUM_TOOL_ACTIONS,
    )


class ToolEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(min_length=1, max_length=MAXIMUM_TOOL_ACTION_LENGTH)
    scope: str = Field(min_length=1, max_length=MAXIMUM_POLICY_SCOPE_LENGTH)


def _tool_problem(error: ToolError, correlation_id: str) -> JSONResponse:
    codes = {
        ToolErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        ToolErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        ToolErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        ToolErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
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


def _policy_problem(error: PolicyError, correlation_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "type": f"https://apistra.dev/problems/{error.code}",
            "title": error.code,
            "detail": error.message,
            "correlation_id": correlation_id,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _policy_error(error: PolicyError | None) -> PolicyError:
    return error or PolicyError(PolicyErrorCode.UNAVAILABLE, "Policy decision is unavailable.")


def _tool(version: ToolVersion) -> dict[str, object]:
    return {
        "tool_id": str(version.tool_id),
        "project_id": str(version.project_id),
        "version": version.version,
        "status": version.status,
        "name": version.name,
        "description": version.description,
        "input_schema": version.input_schema,
        "output_schema": version.output_schema,
        "effect_class": version.effect_class,
        "actions": list(version.actions),
        "created_at": version.created_at.isoformat(),
        "created_by": str(version.created_by),
    }


def _project_allowed(
    projects: ProjectService, owner_id: UUID, project_id: UUID, correlation_id: str
) -> JSONResponse | None:
    if projects.get(owner_id, project_id).error:
        return _tool_problem(
            ToolError(ToolErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE), correlation_id
        )
    return None


def register_tool_routes(  # noqa: C901 - route declarations are deliberately colocated
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    tools: ToolService,
    policies: PolicyService,
) -> None:
    @application.get("/api/v1/projects/{project_id}/tools", tags=[TOOLS_TAG], response_model=None)
    def list_tools(
        project_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        denied = _project_allowed(
            projects, context.session.administrator_id, project_id, request.state.correlation_id
        )
        if denied:
            return denied
        return {
            "items": [
                _tool(item)
                for item in tools.list(context.session.administrator_id, project_id).value or []
            ]
        }

    @application.post(
        "/api/v1/projects/{project_id}/tools",
        tags=[TOOLS_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_tool(
        project_id: UUID,
        payload: ToolVersionRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        denied = _project_allowed(
            projects, context.session.administrator_id, project_id, request.state.correlation_id
        )
        if denied:
            return denied
        result = tools.create_version(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.description,
            payload.input_schema,
            payload.output_schema,
            payload.effect_class.value,
            tuple(payload.actions),
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _tool_problem(
                result.error or ToolError(ToolErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _tool(result.value)

    @application.post(
        "/api/v1/projects/{project_id}/tools/{tool_id}/versions",
        tags=[TOOLS_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_tool_version(
        project_id: UUID,
        tool_id: UUID,
        payload: ToolVersionRequest,
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
        result = tools.create_version(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.description,
            payload.input_schema,
            payload.output_schema,
            payload.effect_class.value,
            tuple(payload.actions),
            idempotency_key or "",
            request.state.correlation_id,
            tool_id=tool_id,
            expected_latest_version=expected,
        )
        if result.error or result.value is None:
            return _tool_problem(
                result.error or ToolError(ToolErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _tool(result.value)

    @application.get(
        "/api/v1/projects/{project_id}/tools/{tool_id}/versions",
        tags=[TOOLS_TAG],
        response_model=None,
    )
    def list_tool_versions(
        project_id: UUID,
        tool_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        result = tools.versions(context.session.administrator_id, project_id, tool_id)
        if result.error:
            return _tool_problem(result.error, request.state.correlation_id)
        return {"items": [_tool(item) for item in result.value or []]}

    @application.post(
        "/api/v1/projects/{project_id}/tools/{tool_id}/versions/{tool_version}:evaluate",
        tags=[TOOLS_TAG],
        response_model=None,
    )
    def evaluate_tool(
        project_id: UUID,
        tool_id: UUID,
        tool_version: int,
        payload: ToolEvaluationRequest,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        tool_result = tools.exact(
            context.session.administrator_id, project_id, tool_id, tool_version
        )
        if tool_result.error or tool_result.value is None:
            return _tool_problem(
                tool_result.error or ToolError(ToolErrorCode.UNAVAILABLE, UNAVAILABLE_MESSAGE),
                request.state.correlation_id,
            )
        tool = tool_result.value
        if payload.action not in tool.actions:
            return _tool_problem(
                ToolError(
                    ToolErrorCode.INVALID_INPUT, "Action is not declared by this tool version."
                ),
                request.state.correlation_id,
            )
        classification = policies.classify(tool.effect_class)
        if classification.error or classification.value is None:
            return _policy_problem(
                _policy_error(classification.error), request.state.correlation_id
            )
        result = policies.evaluate(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            tool_id,
            tool_version,
            classification.value,
            payload.action,
            payload.scope,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _policy_problem(_policy_error(result.error), request.state.correlation_id)
        return {
            "decision": result.value.decision,
            "tool_id": str(tool_id),
            "tool_version": tool_version,
            "action": result.value.action,
            "scope": result.value.scope,
            "exception_id": str(result.value.exception_id) if result.value.exception_id else None,
        }
