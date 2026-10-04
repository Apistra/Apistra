"""HTTP boundary for write-only project secret references."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.entrypoints.api.endpoints import register_endpoint_routes
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain import SecretError, SecretErrorCode, SecretReference
from apistra.modules.identity.domain import SessionContext
from apistra.modules.projects.application import ProjectService

SESSION_COOKIE = "apistra_session"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
PROBLEM_MEDIA_TYPE = "application/problem+json"
CATALOG_TAG = "catalog"
MAXIMUM_SECRET_NAME_LENGTH = 64
MAXIMUM_SECRET_PURPOSE_LENGTH = 256
MAXIMUM_SECRET_VALUE_LENGTH = 65_536
type Authenticate = Callable[[Request, str | None, str | None, bool], SessionContext | JSONResponse]


class SecretCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=MAXIMUM_SECRET_NAME_LENGTH)
    purpose: str = Field(min_length=1, max_length=MAXIMUM_SECRET_PURPOSE_LENGTH)
    value: str = Field(min_length=1, max_length=MAXIMUM_SECRET_VALUE_LENGTH)


class SecretReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1, max_length=MAXIMUM_SECRET_VALUE_LENGTH)


def _problem(error: SecretError, correlation_id: str) -> JSONResponse:
    status_by_code = {
        SecretErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        SecretErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        SecretErrorCode.NAME_CONFLICT: status.HTTP_409_CONFLICT,
        SecretErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        SecretErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
    }
    return JSONResponse(
        status_code=status_by_code[error.code],
        content={
            "type": f"https://apistra.dev/problems/{error.code}",
            "title": error.code,
            "detail": error.message,
            "correlation_id": correlation_id,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _reference(reference: SecretReference) -> dict[str, object]:
    return {
        "id": str(reference.id),
        "project_id": str(reference.project_id),
        "name": reference.name,
        "purpose": reference.purpose,
        "status": reference.status,
        "version": reference.version,
        "envelope_version": reference.envelope.format_version,
        "created_at": reference.created_at.isoformat(),
        "updated_at": reference.updated_at.isoformat(),
    }


def _available_project(
    projects: ProjectService, context: SessionContext, project_id: UUID, correlation_id: str
) -> JSONResponse | None:
    result = projects.get(context.session.administrator_id, project_id)
    if result.error:
        return _problem(
            SecretError(SecretErrorCode.UNAVAILABLE, "Secret reference is unavailable."),
            correlation_id,
        )
    return None


def _register_collection_routes(
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    secrets: SecretService,
) -> None:
    @application.get(
        "/api/v1/projects/{project_id}/secrets", tags=[CATALOG_TAG], response_model=None
    )
    def list_secrets(
        project_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        unavailable = _available_project(
            projects, context, project_id, request.state.correlation_id
        )
        if unavailable:
            return unavailable
        result = secrets.list(context.session.administrator_id, project_id)
        return {"items": [_reference(item) for item in result.value or []]}

    @application.post(
        "/api/v1/projects/{project_id}/secrets",
        tags=[CATALOG_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_secret(
        project_id: UUID,
        payload: SecretCreateRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        unavailable = _available_project(
            projects, context, project_id, request.state.correlation_id
        )
        if unavailable:
            return unavailable
        result = secrets.create(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.purpose,
            payload.value,
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful secret creation returned no reference.")
            return _problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _reference(result.value)


def _register_replace_route(
    application: FastAPI,
    authenticate: Authenticate,
    secrets: SecretService,
) -> None:
    @application.put(
        "/api/v1/projects/{project_id}/secrets/{reference_id}",
        tags=[CATALOG_TAG],
        response_model=None,
    )
    def replace_secret(
        project_id: UUID,
        reference_id: UUID,
        payload: SecretReplaceRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        if_match: str | None = Header(None, alias="if-match"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        version = _expected_version(if_match)
        if version is None:
            return _problem(
                SecretError(
                    SecretErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted secret-reference version.",
                ),
                request.state.correlation_id,
            )
        result = secrets.replace(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            reference_id,
            version,
            payload.value,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful secret replacement returned no reference.")
            return _problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _reference(result.value)


def _register_revoke_route(
    application: FastAPI,
    authenticate: Authenticate,
    secrets: SecretService,
) -> None:
    @application.delete(
        "/api/v1/projects/{project_id}/secrets/{reference_id}",
        tags=[CATALOG_TAG],
        response_model=None,
    )
    def revoke_secret(
        project_id: UUID,
        reference_id: UUID,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        if_match: str | None = Header(None, alias="if-match"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        version = _expected_version(if_match)
        if version is None:
            return _problem(
                SecretError(
                    SecretErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted secret-reference version.",
                ),
                request.state.correlation_id,
            )
        result = secrets.revoke(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            reference_id,
            version,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful secret revocation returned no reference.")
            return _problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _reference(result.value)


def register_catalog_routes(
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    secrets: SecretService,
    endpoints: EndpointService,
) -> None:
    _register_collection_routes(application, authenticate, projects, secrets)
    _register_replace_route(application, authenticate, secrets)
    _register_revoke_route(application, authenticate, secrets)
    register_endpoint_routes(application, authenticate, projects, endpoints)


def _expected_version(if_match: str | None) -> int | None:
    if not if_match:
        return None
    value = if_match.removeprefix("W/").strip().strip('"')
    return int(value) if value.isdigit() and int(value) >= 1 else None
