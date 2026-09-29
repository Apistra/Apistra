"""HTTP composition root for the CAP-00 API shell."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse

from apistra.platform.observability.logging import configure_logging, log_event
from apistra.platform.runtime import RuntimeSettings

settings = RuntimeSettings.from_environment("api")
configure_logging()

app = FastAPI(
    title="Apistra Bootstrap API",
    version=settings.version,
    description="Health-only API shell for CAP-00. No business operations are exposed.",
)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
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


@app.get("/health/live", tags=["health"])
def live() -> dict[str, object]:
    return {"status": "ok", "deployment": settings.marker()}


@app.get("/health/ready", tags=["health"])
def ready() -> JSONResponse:
    if settings.force_not_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "deployment": settings.marker()},
        )
    return JSONResponse(content={"status": "ready", "deployment": settings.marker()})


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def metrics() -> str:
    ready_value = 0 if settings.force_not_ready else 1
    return (
        "# HELP apistra_ready Whether the API is ready.\n"
        "# TYPE apistra_ready gauge\n"
        f'apistra_ready{{service="api"}} {ready_value}\n'
    )
