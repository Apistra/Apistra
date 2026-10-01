import json
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.staging.manual_acceptance import (  # noqa: E402
    FIXTURE_FRESH,
    _environment,
    _initial_state,
    _session_urls,
    _write_private_json,
    build_parser,
    session_directory,
)


def test_session_directory_rejects_path_traversal() -> None:
    with pytest.raises(ValueError):
        session_directory("../outside")


def test_private_json_is_created_with_owner_only_permissions(tmp_path: Path) -> None:
    path = tmp_path / "secret.json"
    _write_private_json(path, {"value": "secret"})

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text()) == {"value": "secret"}


def test_environment_binds_candidate_and_isolated_session() -> None:
    credential = "synthetic-value"
    manifest = {
        "source_commit": "a" * 40,
        "images": {
            "api": {"reference": "api:test"},
            "worker": {"reference": "worker:test"},
            "web": {"reference": "web:test"},
        },
    }
    state = _initial_state(manifest, "acceptance-1", 18_080, 13_000)
    env = _environment(
        state,
        {"database_password": credential, "administrator_password": "unused"},
    )

    assert env["APISTRA_COMMIT"] == "a" * 40
    assert env["APISTRA_COMPOSE_PROJECT"] == "apistra-cap01-acceptance-1"
    assert env["APISTRA_ENVIRONMENT"] == "local-staging-acceptance-1"
    assert env["APISTRA_DB_PASSWORD"] == credential


def test_cli_defaults_to_fresh_fixture() -> None:
    args = build_parser().parse_args(
        ["start", "candidate-manifest.json", "--run-id", "acceptance-1"]
    )

    assert args.fixture == FIXTURE_FRESH
    assert _session_urls(13_000)["bootstrap_url"].endswith("/bootstrap")
