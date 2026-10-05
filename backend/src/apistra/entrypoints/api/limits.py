"""HTTP boundary for immutable resource and budget policy versions."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from apistra.modules.identity.domain import SessionContext
from apistra.modules.policies.public import (
    LimitObservation,
    LimitPolicyVersion,
    PolicyError,
    PolicyErrorCode,
    PolicyResult,
    PolicyService,
)
from apistra.modules.projects.application import ProjectService

SESSION_COOKIE = "apistra_session"
CSRF_HEADER = "x-csrf-token"
ETAG_HEADER = "etag"
PROBLEM_MEDIA_TYPE = "application/problem+json"
LIMITS_TAG = "limits"
MAXIMUM_POLICY_NAME_LENGTH = 128
MAXIMUM_LIMIT_VALUE = 9_007_199_254_740_991
MAXIMUM_WARNING_THRESHOLD_PERCENT = 99
UNAVAILABLE_ERROR = PolicyError(PolicyErrorCode.UNAVAILABLE, "Limit policy version is unavailable.")
type Authenticate = Callable[[Request, str | None, str | None, bool], SessionContext | JSONResponse]


class LimitPolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=MAXIMUM_POLICY_NAME_LENGTH)
    maximum_duration_seconds: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    maximum_calls: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    maximum_tokens: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    maximum_cost_minor_units: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    maximum_concurrency: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    rate_limit_requests: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    rate_limit_window_seconds: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)
    warning_threshold_percent: int | None = Field(
        default=None, ge=1, le=MAXIMUM_WARNING_THRESHOLD_PERCENT
    )


class LimitEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    calls: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    tokens: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    cost_minor_units: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    concurrency: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    requests_in_window: int = Field(ge=0, le=MAXIMUM_LIMIT_VALUE)
    rate_window_seconds: int = Field(gt=0, le=MAXIMUM_LIMIT_VALUE)


def _problem(error: PolicyError, correlation_id: str) -> JSONResponse:
    codes = {
        PolicyErrorCode.INVALID_INPUT: status.HTTP_422_UNPROCESSABLE_CONTENT,
        PolicyErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        PolicyErrorCode.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
        PolicyErrorCode.IDEMPOTENCY_CONFLICT: status.HTTP_409_CONFLICT,
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


def _policy(version: LimitPolicyVersion) -> dict[str, object]:
    return {
        "policy_id": str(version.policy_id),
        "project_id": str(version.project_id),
        "version": version.version,
        "status": version.status,
        "name": version.name,
        "maximum_duration_seconds": version.maximum_duration_seconds,
        "maximum_calls": version.maximum_calls,
        "maximum_tokens": version.maximum_tokens,
        "maximum_cost_minor_units": version.maximum_cost_minor_units,
        "currency": version.currency,
        "maximum_concurrency": version.maximum_concurrency,
        "rate_limit_requests": version.rate_limit_requests,
        "rate_limit_window_seconds": version.rate_limit_window_seconds,
        "warning_threshold_percent": version.warning_threshold_percent,
        "created_at": version.created_at.isoformat(),
        "created_by": str(version.created_by),
    }


def _allowed(
    projects: ProjectService, owner_id: UUID, project_id: UUID, correlation_id: str
) -> JSONResponse | None:
    if projects.get(owner_id, project_id).error:
        return _problem(UNAVAILABLE_ERROR, correlation_id)
    return None


def _create(
    policies: PolicyService,
    context: SessionContext,
    project_id: UUID,
    payload: LimitPolicyRequest,
    idempotency_key: str,
    correlation_id: str,
    policy_id: UUID | None = None,
    expected_latest_version: int = 0,
) -> PolicyResult[LimitPolicyVersion]:
    return policies.create_limit_policy_version(
        context.session.administrator_id,
        context.administrator_username,
        project_id,
        payload.name,
        payload.maximum_duration_seconds,
        payload.maximum_calls,
        payload.maximum_tokens,
        payload.maximum_cost_minor_units,
        payload.currency,
        payload.maximum_concurrency,
        payload.rate_limit_requests,
        payload.rate_limit_window_seconds,
        payload.warning_threshold_percent,
        idempotency_key,
        correlation_id,
        policy_id=policy_id,
        expected_latest_version=expected_latest_version,
    )


def register_limit_routes(  # noqa: C901 - route declarations are deliberately colocated
    application: FastAPI,
    authenticate: Authenticate,
    projects: ProjectService,
    policies: PolicyService,
) -> None:
    @application.get(
        "/api/v1/projects/{project_id}/policies/limits",
        tags=[LIMITS_TAG],
        response_model=None,
    )
    def list_policies(
        project_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        denied = _allowed(
            projects, context.session.administrator_id, project_id, request.state.correlation_id
        )
        if denied:
            return denied
        result = policies.list_limit_policies(context.session.administrator_id, project_id)
        return {"items": [_policy(item) for item in result.value or []]}

    @application.post(
        "/api/v1/projects/{project_id}/policies/limits",
        tags=[LIMITS_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_policy(
        project_id: UUID,
        payload: LimitPolicyRequest,
        request: Request,
        response: Response,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
        idempotency_key: str | None = Header(None, alias="idempotency-key"),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        denied = _allowed(
            projects, context.session.administrator_id, project_id, request.state.correlation_id
        )
        if denied:
            return denied
        result = _create(
            policies,
            context,
            project_id,
            payload,
            idempotency_key or "",
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or UNAVAILABLE_ERROR,
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _policy(result.value)

    @application.post(
        "/api/v1/projects/{project_id}/policies/limits/{policy_id}/versions",
        tags=[LIMITS_TAG],
        status_code=status.HTTP_201_CREATED,
        response_model=None,
    )
    def create_policy_version(
        project_id: UUID,
        policy_id: UUID,
        payload: LimitPolicyRequest,
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
        if (
            not if_match
            or len(if_match) < 3
            or not (if_match.startswith('"') and if_match.endswith('"'))
            or not if_match[1:-1].isdigit()
        ):
            return _problem(
                PolicyError(
                    PolicyErrorCode.INVALID_INPUT,
                    "If-Match must contain the current quoted policy version.",
                ),
                request.state.correlation_id,
            )
        expected = int(if_match[1:-1])
        if policies.exact_limit_policy(
            context.session.administrator_id, project_id, policy_id, expected
        ).error:
            return _problem(UNAVAILABLE_ERROR, request.state.correlation_id)
        result = _create(
            policies,
            context,
            project_id,
            payload,
            idempotency_key or "",
            request.state.correlation_id,
            policy_id,
            expected,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or UNAVAILABLE_ERROR,
                request.state.correlation_id,
            )
        response.headers[ETAG_HEADER] = f'"{result.value.version}"'
        return _policy(result.value)

    @application.get(
        "/api/v1/projects/{project_id}/policies/limits/{policy_id}/versions",
        tags=[LIMITS_TAG],
        response_model=None,
    )
    def list_policy_versions(
        project_id: UUID,
        policy_id: UUID,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, None, False)
        if isinstance(context, JSONResponse):
            return context
        result = policies.limit_policy_versions(
            context.session.administrator_id, project_id, policy_id
        )
        if result.error:
            return _problem(result.error, request.state.correlation_id)
        return {"items": [_policy(item) for item in result.value or []]}

    @application.post(
        "/api/v1/projects/{project_id}/policies/limits/{policy_id}/versions/{policy_version}:publish",
        tags=[LIMITS_TAG],
        response_model=None,
    )
    def publish_policy_version(
        project_id: UUID,
        policy_id: UUID,
        policy_version: int,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        result = policies.publish_limit_policy_version(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            policy_id,
            policy_version,
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or UNAVAILABLE_ERROR,
                request.state.correlation_id,
            )
        return _policy(result.value)

    @application.post(
        "/api/v1/projects/{project_id}/policies/limits/{policy_id}/versions/{policy_version}:evaluate",
        tags=[LIMITS_TAG],
        response_model=None,
    )
    def evaluate_policy(
        project_id: UUID,
        policy_id: UUID,
        policy_version: int,
        payload: LimitEvaluationRequest,
        request: Request,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Header(None, alias=CSRF_HEADER),
    ) -> dict[str, object] | JSONResponse:
        context = authenticate(request, session_token, csrf_token, True)
        if isinstance(context, JSONResponse):
            return context
        result = policies.evaluate_limits(
            context.session.administrator_id,
            context.administrator_username,
            project_id,
            policy_id,
            policy_version,
            LimitObservation(**payload.model_dump()),
            request.state.correlation_id,
        )
        if result.error or result.value is None:
            return _problem(
                result.error or UNAVAILABLE_ERROR,
                request.state.correlation_id,
            )
        return {
            "decision": result.value.decision,
            "action": result.value.action,
            "policy_id": str(result.value.policy_id),
            "policy_version": result.value.policy_version,
            "violated_limits": list(result.value.violated_limits),
            "warned_limits": list(result.value.warned_limits),
            "effect_permitted": result.value.effect_permitted,
        }
