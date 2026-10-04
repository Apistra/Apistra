from __future__ import annotations

import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def contract() -> dict[str, object]:
    return json.loads(
        (ROOT / "contracts/openapi/cap02-endpoints.openapi.json").read_text(encoding="utf-8")
    )


def test_cap02_endpoint_contract_matches_runtime_routes() -> None:
    declared = contract()
    runtime = create_app(RuntimeSettings("api", "0.2.0", "contract", "test")).openapi()
    for path, methods in declared["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])


def test_endpoint_contract_is_closed_bounded_and_never_accepts_secret_material() -> None:
    schema = contract()["components"]["schemas"]["EndpointCreateRequest"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert not {"secret", "token", "api_key", "credential"} & set(schema["properties"])
    assert schema["properties"]["network_profile"]["enum"] == [
        "CLOUD",
        "ON_PREMISE",
        "LOCAL",
    ]
