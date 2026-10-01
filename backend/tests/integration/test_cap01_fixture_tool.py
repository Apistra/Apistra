import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.fixtures.cap_01 import (  # noqa: E402
    FIXTURE_IDS,
    cleanup,
    descriptors,
    run_directory,
    setup,
    verify,
)


def test_cap01_descriptors_are_complete_deterministic_and_secret_safe(
    tmp_path: Path,
) -> None:
    first = setup(tmp_path, "run-a")
    before = {path.name: path.read_bytes() for path in first.iterdir()}
    second = setup(tmp_path, "run-a")
    after = {path.name: path.read_bytes() for path in second.iterdir()}

    assert first == second
    assert before == after
    assert verify(tmp_path, "run-a")
    assert set(descriptors("run-a")) == set(FIXTURE_IDS)

    combined = b"".join(before.values())
    assert b"STAGING_ADMIN_PASSWORD" in combined
    assert b"password_value" not in combined
    assert b"secret_value" not in combined


def test_cap01_isolation_descriptor_has_stable_authorisation_boundary(
    tmp_path: Path,
) -> None:
    directory = setup(tmp_path, "isolation")
    payload = json.loads(directory.joinpath("FX-PRC-01-ISOLATION.json").read_text())
    projects = {project["id"]: project for project in payload["projects"]}

    assert projects["11111111-1111-4111-8111-111111111111"]["authorised"] is True
    assert projects["22222222-2222-4222-8222-222222222222"]["authorised"] is False
    assert payload["expected_state"]["foreign_project_disclosure"] is False
    assert payload["application_mode"] == "guarded-database-reset"


def test_cap01_manifest_detects_tampering(tmp_path: Path) -> None:
    directory = setup(tmp_path, "tamper")
    path = directory / "FX-PRC-01-FRESH.json"
    path.write_text("{}\n", encoding="utf-8")
    assert not verify(tmp_path, "tamper")


def test_cap01_runs_are_isolated_and_cleanup_is_bounded(tmp_path: Path) -> None:
    left = setup(tmp_path, "left")
    right = setup(tmp_path, "right")
    assert left != right

    cleanup(tmp_path, "left")
    assert not left.exists()
    assert right.exists()


def test_cap01_unsafe_run_identifier_is_rejected(tmp_path: Path) -> None:
    try:
        run_directory(tmp_path, "../outside")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe run ID must fail")
