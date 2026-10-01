"""HTTP composition root for health, identity, and isolated project operations."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.entrypoints.api.composition import build_identity_service, build_project_service
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.domain import IdentityError, IdentityErrorCode
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.domain import Project, ProjectError, ProjectErrorCode
from apistra.platform.observability.logging import configure_logging, log_event
from apistra.platform.runtime import RuntimeSettings

configure_logging()
settings = RuntimeSettings.from_environment("api")
SESSION_COOKIE = "apistra_session"


class CredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=12, max_length=1024)


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    key: str = Field(min_length=2, max_length=32)


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
            "correlation_id": correlation_id,
        },
        media_type="application/problem+json",
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
            "correlation_id": correlation_id,
        },
        media_type="application/problem+json",
    )


def _project(project: Project) -> dict[str, object]:
    return {
        "id": str(project.id),
        "name": project.name,
        "key": project.key,
        "status": project.status,
        "version": project.version,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def _expected_version(if_match: str | None) -> int | None:
    if not if_match:
        return None
    value = if_match.removeprefix("W/").strip().strip('"')
    return int(value) if value.isdigit() and int(value) >= 1 else None


def create_app(
    runtime_settings: RuntimeSettings | None = None,
    identity_service: IdentityService | None = None,
    project_service: ProjectService | None = None,
) -> FastAPI:
    configured_settings = runtime_settings

    def current_settings() -> RuntimeSettings:
        return configured_settings or settings

    identity = identity_service or build_identity_service(current_settings())
    projects = project_service or build_project_service(current_settings())
    application = FastAPI(
        title="Apistra API",
        version=current_settings().version,
        description="Local-first API for Apistra administration and process automation.",
    )

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

    @application.get("/health/live", tags=["health"])
    def live() -> dict[str, object]:
        return {"status": "ok", "deployment": current_settings().marker()}

    @application.get("/health/ready", tags=["health"])
    def ready() -> JSONResponse:
        active_settings = current_settings()
        if active_settings.force_not_ready:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "deployment": active_settings.marker()},
            )
        return JSONResponse(content={"status": "ready", "deployment": active_settings.marker()})

    @application.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
    def metrics() -> str:
        ready_value = 0 if current_settings().force_not_ready else 1
        return (
            "# HELP apistra_ready Whether the API is ready.\n"
            "# TYPE apistra_ready gauge\n"
            f'apistra_ready{{service="api"}} {ready_value}\n'
        )

    @application.get("/api/v1/installation", tags=["identity"])
    def installation_status() -> dict[str, bool]:
        return identity.installation_status()

    def session_response(
        result,
        request: Request,
        response: Response,
    ) -> dict[str, object] | JSONResponse:
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        issued = result.value
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
                "id": str(issued.administrator_id),
                "username": issued.administrator_username,
            },
            "csrf_token": issued.csrf_token,
            "expires_at": issued.expires_at.isoformat(),
        }

    @application.post(
        "/api/v1/administrators:bootstrap",
        tags=["identity"],
        status_code=status.HTTP_201_CREATED,
    )
    def bootstrap(credentials: CredentialsRequest, request: Request, response: Response):
        result = identity.bootstrap(
            credentials.username,
            credentials.password,
            request.state.correlation_id,
        )
        return session_response(result, request, response)

    @application.post("/api/v1/sessions", tags=["identity"], status_code=status.HTTP_201_CREATED)
    def create_session(credentials: CredentialsRequest, request: Request, response: Response):
        result = identity.authenticate(
            credentials.username,
            credentials.password,
            request.state.correlation_id,
        )
        return session_response(result, request, response)

    @application.get("/api/v1/session", tags=["identity"])
    def get_session(
        request: Request, session_token: str | None = Cookie(None, alias=SESSION_COOKIE)
    ):
        result = identity.verify_session(session_token)
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        context = result.value
        return {
            "administrator": {
                "id": str(context.session.administrator_id),
                "username": context.administrator_username,
            },
            "expires_at": context.session.expires_at.isoformat(),
        }

    @application.delete(
        "/api/v1/session",
        tags=["identity"],
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    def revoke_session(
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias="x-csrf-token"),
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

    def authenticated(
        request: Request,
        session_token: str | None,
        csrf_token: str | None = None,
        *,
        mutation: bool = False,
    ):
        result = (
            identity.authorize_mutation(session_token, csrf_token)
            if mutation
            else identity.verify_session(session_token)
        )
        if result.error:
            return None, _problem(result.error, request.state.correlation_id)
        return result.value, None

    @application.post("/api/v1/projects", tags=["projects"], status_code=status.HTTP_201_CREATED)
    def create_project(
        payload: ProjectRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias="x-csrf-token"),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ):
        context, problem = authenticated(request, session_token, csrf_token, mutation=True)
        if problem:
            return problem
        result = projects.create(
            context.session.administrator_id,
            context.administrator_username,
            payload.name,
            payload.key,
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error:
            return _project_problem(result.error, request.state.correlation_id)
        response.headers["etag"] = f'"{result.value.version}"'
        return _project(result.value)

    @application.get("/api/v1/projects", tags=["projects"])
    def list_projects(
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ):
        context, problem = authenticated(request, session_token)
        if problem:
            return problem
        result = projects.list(context.session.administrator_id)
        return {"items": [_project(item) for item in result.value]}

    @application.get("/api/v1/projects/{project_id}", tags=["projects"])
    def get_project(
        project_id: uuid.UUID,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ):
        context, problem = authenticated(request, session_token)
        if problem:
            return problem
        result = projects.get(context.session.administrator_id, project_id)
        if result.error:
            return _project_problem(result.error, request.state.correlation_id)
        response.headers["etag"] = f'"{result.value.version}"'
        return _project(result.value)

    @application.patch("/api/v1/projects/{project_id}", tags=["projects"])
    def update_project(
        project_id: uuid.UUID,
        payload: ProjectRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias="x-csrf-token"),
        if_match: str | None = Header(None, alias="if-match"),
    ):
        context, problem = authenticated(request, session_token, csrf_token, mutation=True)
        if problem:
            return problem
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
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            version,
            payload.name,
            payload.key,
            request.state.correlation_id,
        )
        if result.error:
            return _project_problem(result.error, request.state.correlation_id)
        response.headers["etag"] = f'"{result.value.version}"'
        return _project(result.value)

    @application.post("/api/v1/projects/{project_id}:archive", tags=["projects"])
    def archive_project(
        project_id: uuid.UUID,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias="x-csrf-token"),
        if_match: str | None = Header(None, alias="if-match"),
    ):
        context, problem = authenticated(request, session_token, csrf_token, mutation=True)
        if problem:
            return problem
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
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            version,
            request.state.correlation_id,
        )
        if result.error:
            return _project_problem(result.error, request.state.correlation_id)
        response.headers["etag"] = f'"{result.value.version}"'
        return _project(result.value)

    return application


app = create_app()
