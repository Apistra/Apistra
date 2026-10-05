"""Versioned public resource-limit schema and runtime alignment."""

import json
from pathlib import Path

from apistra.entrypoints.api.limits import LimitEvaluationRequest, LimitPolicyRequest
from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

CONTRACT = Path(__file__).resolve().parents[4] / "contracts/openapi/cap02-limits.openapi.json"


def test_limit_contract_paths_and_required_fields_match_runtime() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    runtime = create_app(RuntimeSettings("api", "0.2.0", "commit", "test")).openapi()
    for path, methods in contract["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])
    schemas = contract["components"]["schemas"]
    assert set(schemas["LimitPolicyRequest"]["required"]) <= set(LimitPolicyRequest.model_fields)
    assert set(schemas["LimitEvaluationRequest"]["required"]) == set(
        LimitEvaluationRequest.model_fields
    )
    assert schemas["LimitPolicyRequest"]["additionalProperties"] is False
    assert schemas["LimitEvaluationRequest"]["additionalProperties"] is False
    for field in (
        "maximum_duration_seconds",
        "maximum_calls",
        "maximum_tokens",
        "maximum_cost_minor_units",
        "maximum_concurrency",
        "rate_limit_requests",
        "rate_limit_window_seconds",
    ):
        assert (
            schemas["LimitPolicyRequest"]["properties"][field]["maximum"]
            == (LimitPolicyRequest.model_json_schema()["properties"][field]["maximum"])
        )
    for field in ("calls", "tokens", "cost_minor_units", "concurrency"):
        assert (
            schemas["LimitEvaluationRequest"]["properties"][field]["maximum"]
            == (LimitEvaluationRequest.model_json_schema()["properties"][field]["maximum"])
        )
