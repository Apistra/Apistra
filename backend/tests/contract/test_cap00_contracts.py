import json
import sys
from pathlib import Path

from apistra.entrypoints.api.main import app

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.contracts.validate_repository import repository_contract, validate_contract  # noqa: E402


def test_repository_contract_matches_approved_flow() -> None:
    assert validate_contract(repository_contract(ROOT)) == []


def test_openapi_contract_retains_the_cap00_health_surface() -> None:
    observed = app.openapi()
    expected = json.loads((ROOT / "contracts/openapi/cap00-health.openapi.json").read_text())
    assert set(expected["paths"]) == {"/health/live", "/health/ready"}
    assert set(expected["paths"]) <= set(observed["paths"])


def test_result_bundle_contract_covers_all_reporting_statuses() -> None:
    schema = json.loads((ROOT / "contracts/events/cap00-result-bundle.schema.json").read_text())
    statuses = schema["properties"]["results"]["items"]["properties"]["status"]["enum"]
    assert statuses == ["PASSED", "FAILED", "SKIPPED", "ERROR", "CANCELLED"]


def test_compose_uses_prebuilt_images_and_hardening() -> None:
    compose = (ROOT / "deploy/compose/compose.staging.yml").read_text(encoding="utf-8")
    assert "build:" not in compose
    requirements = (
        "read_only: true",
        'user: "10001:10001"',
        'cap_drop: ["ALL"]',
        "no-new-privileges:true",
        "pids:",
        "memory:",
        "cpus:",
    )
    for requirement in requirements:
        assert requirement in compose


def test_docker_base_images_are_digest_pinned() -> None:
    for path in (ROOT / "backend/Dockerfile", ROOT / "apps/web/Dockerfile"):
        text = path.read_text(encoding="utf-8")
        assert "@sha256:" in text
        assert "USER 10001:10001" in text


def test_bootstrap_shell_has_semantic_accessibility_contract() -> None:
    page = (ROOT / "apps/web/src/app/page.tsx").read_text(encoding="utf-8")
    administration = (ROOT / "apps/web/src/features/administration/public.tsx").read_text(
        encoding="utf-8"
    )
    styles = (ROOT / "apps/web/src/app/styles.css").read_text(encoding="utf-8")
    assert "<main" in page
    assert 'aria-labelledby="bootstrap-title"' in administration
    assert '<h1 id="bootstrap-title">' in administration
    assert 'aria-hidden="true"' in administration
    assert "color-scheme: dark" in styles
    assert "prefers-reduced-motion: reduce" in styles
