from __future__ import annotations

import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def test_cap01_administration_contract_matches_runtime_routes() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap01-administration.openapi.json").read_text(encoding="utf-8")
    )
    runtime = create_app(
        RuntimeSettings("api", "0.1.0", "contract", "test", secure_cookies=True)
    ).openapi()
    for path, methods in contract["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])


def test_project_request_contract_is_closed_and_bounded() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap01-administration.openapi.json").read_text(encoding="utf-8")
    )
    schema = contract["components"]["schemas"]["ProjectRequest"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["name", "key"]
    assert schema["properties"]["name"]["maxLength"] == 128
    assert schema["properties"]["key"]["maxLength"] == 32


def test_audit_contract_and_safe_ui_routes_are_declared() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap01-administration.openapi.json").read_text(encoding="utf-8")
    )
    schema = contract["components"]["schemas"]["AuditEvent"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == [
        "id",
        "event_type",
        "created_at",
        "correlation_id",
        "actor",
        "subject_id",
        "project_id",
        "project_key",
    ]
    assert "/api/v1/audit-events" in contract["paths"]

    web = ROOT / "apps/web/src"
    assert (web / "app/audit/page.tsx").is_file()
    assert (web / "app/projects/[projectId]/page.tsx").is_file()
    administration = (web / "features/administration/public.tsx").read_text(encoding="utf-8")
    for required_copy in (
        "Audit log",
        "Project not found",
        "The project does not exist or you do not have access.",
    ):
        assert required_copy in administration
