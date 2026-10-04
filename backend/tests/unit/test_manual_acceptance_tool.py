import json
import stat
import sys
from argparse import Namespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import tools.staging.manual_acceptance as manual_acceptance  # noqa: E402
from tools.staging.manual_acceptance import (  # noqa: E402
    FIXTURE_FRESH,
    STOPPED,
    ManualAcceptanceError,
    _create_session_directory,
    _environment,
    _initial_state,
    _manual_test_data,
    _session_urls,
    _write_private_json,
    build_parser,
    session_directory,
    status,
    stop,
)
from tools.staging.verify_candidate import write_container_secret_json  # noqa: E402


def test_session_directory_rejects_path_traversal() -> None:
    with pytest.raises(ValueError):
        session_directory("../outside")


def test_private_json_is_created_with_owner_only_permissions(tmp_path: Path) -> None:
    path = tmp_path / "secret.json"
    _write_private_json(path, {"value": "secret"})

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text()) == {"value": "secret"}


def test_container_secret_is_readable_but_parent_remains_owner_only(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "isolated"
    directory.mkdir(mode=0o700)
    path = directory / "key-ring.json"

    write_container_secret_json(path, {"keys": {"local-v1": "synthetic"}})

    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert json.loads(path.read_text()) == {"keys": {"local-v1": "synthetic"}}


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


def test_manual_test_data_resolves_every_case_and_local_url(tmp_path: Path) -> None:
    state = _initial_state(
        {
            "source_commit": "a" * 40,
            "images": {
                "api": {"reference": "api:test"},
                "worker": {"reference": "worker:test"},
                "web": {"reference": "web:test"},
            },
        },
        "acceptance-data",
        18_080,
        13_000,
    )
    state["status"] = "RUNNING"
    state["fixture"] = FIXTURE_FRESH

    data = _manual_test_data(tmp_path, state)

    assert data["active_fixture"] == FIXTURE_FRESH
    assert data["urls"] == {
        "sign_in": "http://127.0.0.1:13000",
        "overview": "http://127.0.0.1:13000",
        "bootstrap": "http://127.0.0.1:13000/bootstrap",
        "audit": "http://127.0.0.1:13000/audit",
        "atlas_project": ("http://127.0.0.1:13000/projects/11111111-1111-4111-8111-111111111111"),
        "orion_project": ("http://127.0.0.1:13000/projects/22222222-2222-4222-8222-222222222222"),
        "unknown_project": ("http://127.0.0.1:13000/projects/99999999-9999-4999-8999-999999999999"),
    }
    assert sorted(data["test_cases"]) == [
        "MT-PRC-01-001",
        "MT-PRC-01-002",
        "MT-PRC-01-003",
        "MT-PRC-01-004",
        "MT-PRC-01-005",
        "MT-PRC-01-006",
    ]
    assert data["credentials"]["administrator_password"]["source_file"] is None
    assert "secret-value" not in json.dumps(data)


def _stopped_state(run_id: str) -> dict[str, object]:
    return {
        "status": STOPPED,
        "run_id": run_id,
        "candidate_commit": "a" * 40,
        "fixture": FIXTURE_FRESH,
        "sign_in_url": "http://127.0.0.1:13000",
        "bootstrap_url": "http://127.0.0.1:13000/bootstrap",
        "project_url_template": "http://127.0.0.1:13000/projects/{project_id}",
    }


def test_existing_run_id_is_rejected_without_changing_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(manual_acceptance, "ACCEPTANCE_ROOT", tmp_path)
    directory = tmp_path / "acceptance-existing"
    directory.mkdir()
    session = directory / "session.json"
    session.write_text(json.dumps(_stopped_state("acceptance-existing")))
    original = session.read_bytes()

    with pytest.raises(ManualAcceptanceError, match="status STOPPED"):
        _create_session_directory("acceptance-existing")

    assert session.read_bytes() == original
    assert sorted(path.name for path in directory.iterdir()) == ["session.json"]


def test_cli_reports_existing_run_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(manual_acceptance, "ACCEPTANCE_ROOT", tmp_path)
    directory = tmp_path / "acceptance-existing"
    directory.mkdir()
    (directory / "session.json").write_text(json.dumps(_stopped_state("acceptance-existing")))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_acceptance.py",
            "start",
            "candidate-manifest.json",
            "--run-id",
            "acceptance-existing",
        ],
    )

    assert manual_acceptance.main() == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "failed safely" in captured.err
    assert "status STOPPED" in captured.err
    assert "Traceback" not in captured.err


def test_status_reads_stopped_session_after_secrets_are_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(manual_acceptance, "ACCEPTANCE_ROOT", tmp_path)
    directory = tmp_path / "acceptance-stopped"
    directory.mkdir()
    (directory / "session.json").write_text(json.dumps(_stopped_state("acceptance-stopped")))

    assert status(Namespace(run_id="acceptance-stopped")) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == STOPPED
    assert output["run_id"] == "acceptance-stopped"
    assert output["password_file"] is None


def test_stop_is_idempotent_after_runtime_secrets_are_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(manual_acceptance, "ACCEPTANCE_ROOT", tmp_path)
    directory = tmp_path / "acceptance-stopped"
    directory.mkdir()
    (directory / "session.json").write_text(json.dumps(_stopped_state("acceptance-stopped")))

    assert stop(Namespace(run_id="acceptance-stopped")) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == STOPPED
    assert output["password_file"] is None
