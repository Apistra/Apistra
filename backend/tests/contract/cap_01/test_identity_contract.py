from apistra.entrypoints.api.main import create_app
from apistra.platform.runtime import RuntimeSettings


def test_identity_openapi_contract_is_versioned_and_complete() -> None:
    app = create_app(RuntimeSettings("api", "0.1.0", "commit", "test"))
    schema = app.openapi()
    assert schema["info"]["version"] == "0.1.0"
    assert {
        "/api/v1/installation",
        "/api/v1/administrators:bootstrap",
        "/api/v1/sessions",
        "/api/v1/session",
    } <= schema["paths"].keys()
    credentials = schema["components"]["schemas"]["CredentialsRequest"]
    assert credentials["additionalProperties"] is False
    assert credentials["properties"]["password"]["maxLength"] == 1024
