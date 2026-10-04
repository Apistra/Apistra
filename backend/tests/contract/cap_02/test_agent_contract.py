import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def test_agent_contract_paths_and_schema_match_runtime() -> None:
    contract = json.loads((ROOT / "contracts/openapi/cap02-agents.openapi.json").read_text())
    runtime = create_app(RuntimeSettings("api", "0.2.0", "commit", "test")).openapi()
    for path, methods in contract["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])
    schema = contract["components"]["schemas"]["AgentVersionRequest"]
    runtime_schema = runtime["components"]["schemas"]["AgentVersionRequest"]
    assert set(schema["required"]) == set(runtime_schema["required"])
    assert set(schema["properties"]) == set(runtime_schema["properties"])
