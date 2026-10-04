from __future__ import annotations

import json
from pathlib import Path

from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings

ROOT = Path(__file__).resolve().parents[4]


def test_cap02_secret_contract_matches_runtime_routes() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap02-secrets.openapi.json").read_text(encoding="utf-8")
    )
    runtime = create_app(RuntimeSettings("api", "0.2.0", "contract", "test")).openapi()
    for path, methods in contract["paths"].items():
        assert path in runtime["paths"]
        assert set(methods) <= set(runtime["paths"][path])


def test_secret_write_contract_is_closed_bounded_and_write_only() -> None:
    contract = json.loads(
        (ROOT / "contracts/openapi/cap02-secrets.openapi.json").read_text(encoding="utf-8")
    )
    schema = contract["components"]["schemas"]["SecretCreateRequest"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["name", "purpose", "value"]
    assert schema["properties"]["value"] == {
        "type": "string",
        "minLength": 1,
        "maxLength": 65536,
        "writeOnly": True,
    }
    public_fields = contract["components"]["schemas"]["SecretReference"]["properties"]
    assert not {"value", "ciphertext", "nonce", "key_id"} & set(public_fields)
