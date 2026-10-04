"""HTTP boundary for project-scoped model and embedding endpoints."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.domain.endpoints import (
    EndpointError,
    EndpointErrorCode,
    EndpointPurpose,
    ModelEndpoint,
    NetworkProfile,
    ProviderProtocol,
)
from apistra.modules.identity.domain import SessionContext
from apistra.modules.projects.application import ProjectService

SESSION_COOKIE = "apistra_session"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
PROBLEM_MEDIA_TYPE = "application/problem+json"
ENDPOINT_TAG = "endpoints"
MAXIMUM_ENDPOINT_NAME_LENGTH = 64
MAXIMUM_BASE_URL_LENGTH = 2048
MAXIMUM_MODEL_IDENTIFIER_LENGTH = 256
type Authenticate = Callable[[Request, str | None, str | None, bool], SessionContext | JSONResponse]


class EndpointCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=MAXIMUM_ENDPOINT_NAME_LENGTH)
    purpose: EndpointPurpose
    provider_protocol: ProviderProtocol
    base_url: str = Field(min_length=1, max_length=MAXIMUM_BASE_URL_LENGTH)
    model_identifier: str = Field(min_length=1, max_length=MAXIMUM_MODEL_IDENTIFIER_LENGTH)
    secret_reference_id: UUID
    network_profile: NetworkProfile


def _problem(error: EndpointError, correlation_id: str) -> JSONResponse:
    status_by_code = {
        EndpointErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        EndpointErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        EndpointErrorCode.NAME_CONFLICT: status.HTTP_409_CONFLICT,
        EndpointErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        EndpointErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
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


def _endpoint(endpoint: ModelEndpoint) -> dict[str, object]:
    return {
        "id": str(endpoint.id),
        "project_id": str(endpoint.project_id),
        "name": endpoint.name,
        "purpose": endpoint.purpose,
        "provider_protocol": endpoint.provider_protocol,
        "base_url": endpoint.base_url,
        "model_identifier": endpoint.model_identifier,
        "secret_reference_id": str(endpoint.secret_reference_id),
        "network_profile": endpoint.network_profile,
        "status": endpoint.status,
        "version": endpoint.version,
        "last_probe_outcome": endpoint.last_probe_outcome,
        "created_at": endpoint.created_at.isoformat(),
        "updated_at": endpoint.updated_at.isoformat(),
    }


def _expected_version(if_match: str | None) -> int | None:
    if not if_match:
        return None
    value = if_match.removeprefix("W/").strip().strip('"')
    return int(value) if value.isdigit() and int(value) >= 1 else None


def _register_collection_routes(
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    endpoints: EndpointService,
) -> None:
    @application.get(
        "/api/v1/projects/{project_id}/endpoints",
        tags=[ENDPOINT_TAG],
        response_model=None,
    )
    def list_endpoints(
        project_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        if projects.get(context.session.administrator_id, project_id).error:
            return _problem(
                EndpointError(EndpointErrorCode.UNAVAILABLE, "Endpoint is unavailable."),
                request.state.correlation_id,
            )
        result = endpoints.list(context.session.administrator_id, project_id)
        return {"items": [_endpoint(item) for item in result.value or []]}

    @application.post(
        "/api/v1/projects/{project_id}/endpoints",
        tags=[ENDPOINT_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_endpoint(
        project_id: UUID,
        payload: EndpointCreateRequest,
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
                EndpointError(EndpointErrorCode.UNAVAILABLE, "Endpoint is unavailable."),
                request.state.correlation_id,
            )
        result = endpoints.create(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            payload.name,
            payload.purpose,
            payload.provider_protocol,
            payload.base_url,
            payload.model_identifier,
            payload.secret_reference_id,
            payload.network_profile,
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful endpoint creation returned no endpoint.")
            return _problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _endpoint(result.value)


def _register_test_route(
    application: FastAPI,
    authenticate: Authenticate,
    endpoints: EndpointService,
) -> None:

    @application.post(
        "/api/v1/projects/{project_id}/endpoints/{endpoint_id}:test",
        tags=[ENDPOINT_TAG],
        response_model=None,
    )
    def test_connection(
        project_id: UUID,
        endpoint_id: UUID,
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
                EndpointError(
                    EndpointErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted endpoint version.",
                ),
                request.state.correlation_id,
            )
        result = endpoints.test_connection(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            endpoint_id,
            version,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful connection test returned no endpoint.")
            return _problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _endpoint(result.value)


def register_endpoint_routes(
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    endpoints: EndpointService,
) -> None:
    _register_collection_routes(application, authenticate, projects, endpoints)
    _register_test_route(application, authenticate, endpoints)
