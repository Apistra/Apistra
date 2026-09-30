import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.fixtures.cap00 import cleanup, fixture, run_directory, setup  # noqa: E402


def test_fixture_setup_is_idempotent_and_contains_references_only(tmp_path: Path) -> None:
    first = setup(tmp_path, "run-a")
    before = first.joinpath("fixture.json").read_bytes()
    second = setup(tmp_path, "run-a")
    assert first == second
    assert before == second.joinpath("fixture.json").read_bytes()
    payload = json.loads(before)
    assert payload["synthetic"] is True
    assert payload["credential_references"] == ["env:APISTRA_TEST_CREDENTIAL"]


def test_concurrent_runs_are_isolated(tmp_path: Path) -> None:
    left = fixture("left")
    right = fixture("right")
    assert left["administrator"]["external_id"] != right["administrator"]["external_id"]
    assert run_directory(tmp_path, "left") != run_directory(tmp_path, "right")


def test_cleanup_only_removes_named_run(tmp_path: Path) -> None:
    left = setup(tmp_path, "left")
    right = setup(tmp_path, "right")
    cleanup(tmp_path, "left")
    assert not left.exists()
    assert right.exists()


def test_unsafe_run_identifier_is_rejected(tmp_path: Path) -> None:
    try:
        run_directory(tmp_path, "../outside")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe run ID must fail")
