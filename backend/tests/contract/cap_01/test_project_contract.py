from __future__ import annotations

import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def test_cap01_administration_contract_matches_runtime_routes() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap01-administration.openapi.json").read_text(
            encoding="utf-8"
        )
    )
    runtime = create_app(
        RuntimeSettings("api", "0.1.0", "contract", "test", secure_cookies=True)
    ).openapi()
    for path, methods in contract["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])


def test_project_request_contract_is_closed_and_bounded() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap01-administration.openapi.json").read_text(
            encoding="utf-8"
        )
    )
    schema = contract["components"]["schemas"]["ProjectRequest"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["name", "key"]
    assert schema["properties"]["name"]["maxLength"] == 128
    assert schema["properties"]["key"]["maxLength"] == 32
