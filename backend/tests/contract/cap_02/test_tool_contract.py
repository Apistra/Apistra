from __future__ import annotations

import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def contract() -> dict[str, object]:
    return json.loads(
        (ROOT / "contracts/openapi/cap02-tools.openapi.json").read_text(encoding="utf-8")
    )


def test_cap02_tool_contract_matches_runtime_routes() -> None:
    declared = contract()
    runtime = create_app(RuntimeSettings("api", "0.2.0", "contract", "test")).openapi()
    for path, methods in declared["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])


def test_tool_contract_is_closed_bounded_and_requires_explicit_effect() -> None:
    schemas = contract()["components"]["schemas"]
    version = schemas["ToolVersionRequest"]
    evaluation = schemas["ToolEvaluationRequest"]
    assert version["additionalProperties"] is False
    assert evaluation["additionalProperties"] is False
    assert version["properties"]["effect_class"]["enum"] == [
        "READ",
        "WRITE",
        "ADMINISTRATIVE",
    ]
    assert version["properties"]["actions"]["maxItems"] == 128
    assert evaluation["properties"]["scope"]["maxLength"] == 512
