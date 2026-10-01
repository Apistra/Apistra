import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.architecture.python_rules import analyse_source_root  # noqa: E402


def test_backend_obeys_python_architecture_rules() -> None:
    violations = analyse_source_root(REPOSITORY_ROOT / "backend/src")
    assert violations == [], "\n".join(violation.render() for violation in violations)


def test_allowed_fixture_passes() -> None:
    fixture = REPOSITORY_ROOT / "tests/architecture-fixtures/python/allowed/src"
    violations = analyse_source_root(fixture)
    assert violations == [], "\n".join(violation.render() for violation in violations)


def test_forbidden_fixture_proves_rules_are_active() -> None:
    fixture = REPOSITORY_ROOT / "tests/architecture-fixtures/python/forbidden/src"
    violations = analyse_source_root(fixture)
    rules = {violation.rule for violation in violations}
    assert {"ARCH-001", "ARCH-LAYERS", "ARCH-MODULE-PUBLIC", "ARCH-013"} <= rules


def test_empty_scope_fails_closed(tmp_path: Path) -> None:
    violations = analyse_source_root(tmp_path)
    assert [violation.rule for violation in violations] == ["ARCH-SCOPE"]
