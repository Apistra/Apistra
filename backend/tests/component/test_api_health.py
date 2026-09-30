from fastapi.testclient import TestClient

from apistra.entrypoints.api import main
from apistra.platform.runtime import RuntimeSettings

client = TestClient(main.app)


def test_liveness_exposes_deployment_marker_and_security_headers() -> None:
    response = client.get("/health/live", headers={"x-correlation-id": "cap00-test"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["deployment"]["service"] == "api"
    assert response.headers["x-correlation-id"] == "cap00-test"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_readiness_is_ready_by_default() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_fails_closed_when_forced(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "settings",
        RuntimeSettings("api", "0.0.1", "abc", "test", force_not_ready=True),
    )
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_metrics_reflect_forced_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "settings",
        RuntimeSettings("api", "0.0.1", "abc", "test", force_not_ready=True),
    )
    assert 'apistra_ready{service="api"} 0' in client.get("/metrics").text


def test_unknown_business_route_is_absent() -> None:
    assert client.post("/api/v1/workflows").status_code == 404


def test_metrics_are_machine_readable() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert 'apistra_ready{service="api"} 1' in response.text
