"""HTTP composition root for health, identity, and isolated project operations."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.entrypoints.api.agents import register_agent_routes
from apistra.entrypoints.api.catalog import register_catalog_routes
from apistra.entrypoints.api.composition import (
    build_agent_service,
    build_endpoint_service,
    build_identity_service,
    build_project_service,
    build_secret_service,
)
from apistra.modules.agents.application import AgentService
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.identity.application import IdentityService, OperationResult
from apistra.modules.identity.domain import (
    IdentityError,
    IdentityErrorCode,
    IssuedSession,
    SessionContext,
)
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.domain import Project, ProjectError, ProjectErrorCode
from apistra.platform.observability.logging import configure_logging, log_event
from apistra.platform.runtime import RuntimeSettings

configure_logging()
settings = RuntimeSettings.from_environment("api")
SESSION_COOKIE = "apistra_session"
PROBLEM_MEDIA_TYPE = "application/problem+json"
IDENTITY_TAG = "identity"
PROJECTS_TAG = "projects"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
FIELD_ID = "id"
FIELD_STATUS = "status"
FIELD_CREATED_AT = "created_at"
FIELD_CORRELATION_ID = "correlation_id"
FIELD_EVENT_TYPE = "event_type"
FIELD_ACTOR = "actor"
FIELD_SUBJECT_ID = "subject_id"
FIELD_PROJECT_ID = "project_id"
FIELD_PROJECT_KEY = "project_key"
MINIMUM_USERNAME_LENGTH = 3
MAXIMUM_USERNAME_LENGTH = 128
MINIMUM_PASSWORD_LENGTH = 12
MAXIMUM_PASSWORD_LENGTH = 1024
MAXIMUM_PROJECT_NAME_LENGTH = 128
MAXIMUM_PROJECT_KEY_LENGTH = 32


class CredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=MINIMUM_USERNAME_LENGTH,
        max_length=MAXIMUM_USERNAME_LENGTH,
    )
    password: str = Field(
        min_length=MINIMUM_PASSWORD_LENGTH,
        max_length=MAXIMUM_PASSWORD_LENGTH,
    )


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=MAXIMUM_PROJECT_NAME_LENGTH)
    key: str = Field(min_length=2, max_length=MAXIMUM_PROJECT_KEY_LENGTH)


def _problem(error: IdentityError, correlation_id: str) -> JSONResponse:
    status_by_code = {
        IdentityErrorCode.BOOTSTRAP_CLOSED: status.HTTP_409_CONFLICT,
        IdentityErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        IdentityErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
        IdentityErrorCode.SESSION_INVALID: status.HTTP_401_UNAUTHORIZED,
        IdentityErrorCode.CSRF_INVALID: status.HTTP_403_FORBIDDEN,
    }
    return JSONResponse(
        status_code=status_by_code[error.code],
        content={
            "type": f"https://apistra.dev/problems/{error.code}",
            "title": error.code,
            "detail": error.message,
            FIELD_CORRELATION_ID: correlation_id,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _project_problem(error: ProjectError, correlation_id: str) -> JSONResponse:
    status_by_code = {
        ProjectErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        ProjectErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ProjectErrorCode.KEY_CONFLICT: status.HTTP_409_CONFLICT,
        ProjectErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        ProjectErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
    }
    return JSONResponse(
        status_code=status_by_code[error.code],
        content={
            "type": f"https://apistra.dev/problems/{error.code}",
            "title": error.code,
            "detail": error.message,
            FIELD_CORRELATION_ID: correlation_id,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _project(project: Project) -> dict[str, object]:
    return {
        FIELD_ID: str(project.id),
        "name": project.name,
        "key": project.key,
        FIELD_STATUS: project.status,
        "version": project.version,
        FIELD_CREATED_AT: project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def _expected_version(if_match: str | None) -> int | None:
    if not if_match:
        return None
    value = if_match.removeprefix("W/").strip().strip('"')
    return int(value) if value.isdigit() and int(value) >= 1 else None


def _register_request_context(application: FastAPI) -> None:
    @application.middleware("http")
    async def request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        response.headers["cache-control"] = "no-store"
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        log_event(
            "http.request.completed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        return response


def _register_health_routes(
    application: FastAPI, current_settings: Callable[[], RuntimeSettings]
) -> None:
    @application.get("/health/live", tags=["health"])
    def live() -> dict[str, object]:
        return {FIELD_STATUS: "ok", "deployment": current_settings().marker()}

    @application.get("/health/ready", tags=["health"])
    def ready() -> JSONResponse:
        active_settings = current_settings()
        if active_settings.force_not_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={FIELD_STATUS: "not_ready", "deployment": active_settings.marker()},
            )
        return JSONResponse(content={FIELD_STATUS: "ready", "deployment": active_settings.marker()})

    @application.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
    def metrics() -> str:
        ready_value = 0 if current_settings().force_not_ready else 1
        return (
            "# HELP apistra_ready Whether the API is ready.\n"
            "# TYPE apistra_ready gauge\n"
            f'apistra_ready{{service="api"}} {ready_value}\n'
        )


def _session_response(
    result: OperationResult[IssuedSession],
    request: Request,
    response: Response,
    current_settings: Callable[[], RuntimeSettings],
) -> dict[str, object] | JSONResponse:
    if result.error:
        return _problem(result.error, request.state.correlation_id)
    issued = result.value
    if issued is None:
        raise RuntimeError("Successful session operation returned no issued session.")
    active_settings = current_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=issued.raw_token,
        httponly=True,
        secure=active_settings.secure_cookies,
        samesite="strict",
        max_age=active_settings.session_ttl_seconds,
        path="/",
    )
    return {
        "administrator": {
            FIELD_ID: str(issued.administrator_id),
            "username": issued.administrator_username,
        },
        "csrf_token": issued.csrf_token,
        "expires_at": issued.expires_at.isoformat(),
    }


def _register_identity_creation_routes(
    application: FastAPI,
    identity: IdentityService,
    current_settings: Callable[[], RuntimeSettings],
) -> None:
    @application.get("/api/v1/installation", tags=[IDENTITY_TAG])
    def installation_status() -> dict[str, bool]:
        return identity.installation_status()

    @application.post(
        "/api/v1/administrators:bootstrap",
        tags=[IDENTITY_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def bootstrap(
        credentials: CredentialsRequest, request: Request, response: Response
    ) -> dict[str, object] | JSONResponse:
        result = identity.bootstrap(
            credentials.username,
            credentials.password,
            request.state.correlation_id,
        )
        return _session_response(result, request, response, current_settings)

    @application.post(
        "/api/v1/sessions",
        tags=[IDENTITY_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_session(
        credentials: CredentialsRequest, request: Request, response: Response
    ) -> dict[str, object] | JSONResponse:
        result = identity.authenticate(
            credentials.username,
            credentials.password,
            request.state.correlation_id,
        )
        return _session_response(result, request, response, current_settings)


def _register_identity_session_routes(
    application: FastAPI,
    identity: IdentityService,
    current_settings: Callable[[], RuntimeSettings],
) -> None:

    @application.get("/api/v1/session", tags=[IDENTITY_TAG], response_model=None)
    def get_session(
        request: Request, session_token: str | None = Cookie(None, alias=SESSION_COOKIE)
    ) -> dict[str, object] | JSONResponse:
        result = identity.verify_session(session_token)
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        context = result.value
        if context is None:
            raise RuntimeError("Successful session verification returned no context.")
        return {
            "administrator": {
                FIELD_ID: str(context.session.administrator_id),
                "username": context.administrator_username,
            },
            "expires_at": context.session.expires_at.isoformat(),
        }

    @application.delete(
        "/api/v1/session",
        tags=[IDENTITY_TAG],
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    def revoke_session(
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
    ) -> Response:
        result = identity.revoke_session(
            session_token,
            csrf_token,
            request.state.correlation_id,
        )
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        active_settings = current_settings()
        response.delete_cookie(
            SESSION_COOKIE,
            path="/",
            secure=active_settings.secure_cookies,
            httponly=True,
            samesite="strict",
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return response


def _authenticated(
    identity: IdentityService,
    request: Request,
    session_token: str | None,
    csrf_token: str | None = None,
    *,
    mutation: bool = False,
) -> SessionContext | JSONResponse:
    result = (
        identity.authorize_mutation(session_token, csrf_token)
        if mutation
        else identity.verify_session(session_token)
    )
    if result.error:
        return _problem(result.error, request.state.correlation_id)
    if result.value is None:
        raise RuntimeError("Successful authentication returned no session context.")
    return result.value


def _register_project_collection_routes(
    application: FastAPI,
    identity: IdentityService,
    projects: ProjectService,
) -> None:

    @application.post(
        "/api/v1/projects",
        tags=[PROJECTS_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_project(
        payload: ProjectRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token, csrf_token, mutation=True)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        result = projects.create(
            authenticated.session.administrator_id,
            authenticated.administrator_username,
            payload.name,
            payload.key,
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful project creation returned no project.")
            return _project_problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _project(result.value)

    @application.get("/api/v1/projects", tags=[PROJECTS_TAG], response_model=None)
    def list_projects(
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        result = projects.list(authenticated.session.administrator_id)
        if result.value is None:
            raise RuntimeError("Successful project listing returned no collection.")
        return {"items": [_project(item) for item in result.value]}


def _register_audit_route(
    application: FastAPI,
    identity: IdentityService,
    projects: ProjectService,
    secrets: SecretService,
    endpoints: EndpointService,
    agents: AgentService,
) -> None:
    @application.get("/api/v1/audit-events", tags=["audit"], response_model=None)
    def list_audit_events(
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        administrator_id = authenticated.session.administrator_id
        identity_events: list[dict[str, object]] = [
            {
                FIELD_ID: str(event.id),
                FIELD_EVENT_TYPE: event.event_type,
                FIELD_CREATED_AT: event.created_at.isoformat(),
                FIELD_CORRELATION_ID: event.correlation_id,
                FIELD_ACTOR: event.actor_username,
                FIELD_SUBJECT_ID: str(event.subject_id) if event.subject_id else None,
                "installation_id": event.details.get("installation_id"),
                FIELD_PROJECT_ID: None,
                FIELD_PROJECT_KEY: None,
            }
            for event in identity.audit_events(administrator_id)
        ]
        project_event_result = projects.audit_events(administrator_id)
        if project_event_result.value is None:
            raise RuntimeError("Successful project audit query returned no collection.")
        project_events: list[dict[str, object]] = [
            {
                FIELD_ID: str(event.id),
                FIELD_EVENT_TYPE: event.event_type,
                FIELD_CREATED_AT: event.created_at.isoformat(),
                FIELD_CORRELATION_ID: event.correlation_id,
                FIELD_ACTOR: event.actor_username,
                FIELD_SUBJECT_ID: str(event.project_id),
                FIELD_PROJECT_ID: str(event.project_id),
                FIELD_PROJECT_KEY: event.project_key,
            }
            for event in project_event_result.value
        ]
        secret_event_result = secrets.audit_events(administrator_id)
        if secret_event_result.value is None:
            raise RuntimeError("Successful secret audit query returned no collection.")
        secret_events: list[dict[str, object]] = [
            {
                FIELD_ID: str(event.id),
                FIELD_EVENT_TYPE: event.event_type,
                FIELD_CREATED_AT: event.created_at.isoformat(),
                FIELD_CORRELATION_ID: event.correlation_id,
                FIELD_ACTOR: event.actor_username,
                FIELD_SUBJECT_ID: str(event.secret_reference_id),
                FIELD_PROJECT_ID: str(event.project_id),
                FIELD_PROJECT_KEY: None,
            }
            for event in secret_event_result.value
        ]
        endpoint_event_result = endpoints.audit_events(administrator_id)
        if endpoint_event_result.value is None:
            raise RuntimeError("Successful endpoint audit query returned no collection.")
        endpoint_events: list[dict[str, object]] = [
            {
                FIELD_ID: str(event.id),
                FIELD_EVENT_TYPE: event.event_type,
                FIELD_CREATED_AT: event.created_at.isoformat(),
                FIELD_CORRELATION_ID: event.correlation_id,
                FIELD_ACTOR: event.actor_username,
                FIELD_SUBJECT_ID: str(event.endpoint_id),
                FIELD_PROJECT_ID: str(event.project_id),
                FIELD_PROJECT_KEY: None,
            }
            for event in endpoint_event_result.value
        ]
        agent_event_result = agents.audit_events(administrator_id)
        if agent_event_result.value is None:
            raise RuntimeError("Successful agent audit query returned no collection.")
        agent_events: list[dict[str, object]] = [
            {
                FIELD_ID: str(event.id),
                FIELD_EVENT_TYPE: event.event_type,
                FIELD_CREATED_AT: event.created_at.isoformat(),
                FIELD_CORRELATION_ID: event.correlation_id,
                FIELD_ACTOR: event.actor_username,
                FIELD_SUBJECT_ID: str(event.agent_id),
                FIELD_PROJECT_ID: str(event.project_id),
                FIELD_PROJECT_KEY: None,
            }
            for event in agent_event_result.value
        ]
        events = sorted(
            [*identity_events, *project_events, *secret_events, *endpoint_events, *agent_events],
            key=lambda event: (
                str(event[FIELD_CREATED_AT]),
                str(event[FIELD_ID]),
            ),
            reverse=True,
        )
        return {"items": events}


def _register_project_read_route(
    application: FastAPI,
    identity: IdentityService,
    projects: ProjectService,
) -> None:
    @application.get("/api/v1/projects/{project_id}", tags=[PROJECTS_TAG], response_model=None)
    def get_project(
        project_id: uuid.UUID,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        result = projects.get(authenticated.session.administrator_id, project_id)
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful project lookup returned no project.")
            return _project_problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _project(result.value)


def _register_project_update_route(
    application: FastAPI,
    identity: IdentityService,
    projects: ProjectService,
) -> None:
    @application.patch("/api/v1/projects/{project_id}", tags=[PROJECTS_TAG], response_model=None)
    def update_project(
        project_id: uuid.UUID,
        payload: ProjectRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        if_match: str | None = Header(None, alias="if-match"),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token, csrf_token, mutation=True)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        version = _expected_version(if_match)
        if version is None:
            return _project_problem(
                ProjectError(
                    ProjectErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted project version.",
                ),
                request.state.correlation_id,
            )
        result = projects.update(
            authenticated.session.administrator_id,
            authenticated.administrator_username,
            project_id,
            version,
            payload.name,
            payload.key,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful project update returned no project.")
            return _project_problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _project(result.value)


def _register_project_archive_route(
    application: FastAPI,
    identity: IdentityService,
    projects: ProjectService,
) -> None:
    @application.post(
        "/api/v1/projects/{project_id}:archive",
        tags=[PROJECTS_TAG],
        response_model=None,
    )
    def archive_project(
        project_id: uuid.UUID,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        if_match: str | None = Header(None, alias="if-match"),
    ) -> dict[str, object] | JSONResponse:
        authenticated = _authenticated(identity, request, session_token, csrf_token, mutation=True)
        if isinstance(authenticated, JSONResponse):
            return authenticated
        version = _expected_version(if_match)
        if version is None:
            return _project_problem(
                ProjectError(
                    ProjectErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted project version.",
                ),
                request.state.correlation_id,
            )
        result = projects.archive(
            authenticated.session.administrator_id,
            authenticated.administrator_username,
            project_id,
            version,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            if result.error is None:
                raise RuntimeError("Successful project archival returned no project.")
            return _project_problem(result.error, request.state.correlation_id)
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _project(result.value)


def create_app(
    runtime_settings: RuntimeSettings | None = None,
    identity_service: IdentityService | None = None,
    project_service: ProjectService | None = None,
    secret_service: SecretService | None = None,
    endpoint_service: EndpointService | None = None,
    agent_service: AgentService | None = None,
) -> FastAPI:
    configured_settings = runtime_settings

    def current_settings() -> RuntimeSettings:
        return configured_settings or settings

    identity = identity_service or build_identity_service(current_settings())
    projects = project_service or build_project_service(current_settings())
    secrets = secret_service or build_secret_service(current_settings())
    endpoints = endpoint_service or build_endpoint_service(current_settings(), secrets)
    agents = agent_service or build_agent_service(current_settings(), endpoints)
    application = FastAPI(
        title="Apistra API",
        version=current_settings().version,
        description="Local-first API for Apistra administration and process automation.",
    )
    _register_request_context(application)
    _register_health_routes(application, current_settings)
    _register_identity_creation_routes(application, identity, current_settings)
    _register_identity_session_routes(application, identity, current_settings)
    _register_project_collection_routes(application, identity, projects)
    _register_audit_route(application, identity, projects, secrets, endpoints, agents)
    _register_project_read_route(application, identity, projects)
    _register_project_update_route(application, identity, projects)
    _register_project_archive_route(application, identity, projects)
    register_catalog_routes(
        application,
        lambda request, token, csrf, mutation: _authenticated(
            identity, request, token, csrf, mutation=mutation
        ),
        projects,
        secrets,
        endpoints,
    )
    register_agent_routes(
        application,
        lambda request, token, csrf, mutation: _authenticated(
            identity, request, token, csrf, mutation=mutation
        ),
        projects,
        agents,
    )

    return application


app = create_app()
