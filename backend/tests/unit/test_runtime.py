from apistra.modules.projects.public import ProjectContext
from apistra.platform.runtime import RuntimeSettings


def test_deployment_marker_contains_only_public_identity() -> None:
    settings = RuntimeSettings(service="api", version="0.0.1", commit="abc123", environment="test")
    assert settings.marker() == {
        "service": "api",
        "version": "0.0.1",
        "commit": "abc123",
        "environment": "test",
    }


def test_public_project_context_is_an_immutable_value() -> None:
    assert ProjectContext("project-1").project_id == "project-1"
