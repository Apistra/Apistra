from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_required_repository_boundaries_exist() -> None:
    expected_directories = (
        "apps/web",
        "backend",
        "contracts/openapi",
        "contracts/workflow",
        "contracts/events",
        "contracts/connectors",
        "connector-sdk/python",
        "deploy/compose",
        "engineering/softwaretest",
        "tests/architecture-fixtures",
        "tools/architecture",
    )

    missing = [
        directory
        for directory in expected_directories
        if not (REPOSITORY_ROOT / directory).is_dir()
    ]
    assert missing == [], f"Missing approved repository boundaries: {missing}"


def test_runtime_and_package_manager_versions_are_pinned() -> None:
    assert (REPOSITORY_ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
    assert (REPOSITORY_ROOT / ".node-version").read_text(encoding="utf-8").strip() == "24.19.0"


def test_backend_has_explicit_composition_roots() -> None:
    package_root = REPOSITORY_ROOT / "backend/src/apistra"
    expected = (
        package_root / "entrypoints/api/composition.py",
        package_root / "entrypoints/worker/composition.py",
    )
    assert all(path.is_file() for path in expected)


def test_engineering_adapter_is_outside_runtime_package() -> None:
    runtime_root = REPOSITORY_ROOT / "backend/src/apistra"
    engineering_root = REPOSITORY_ROOT / "engineering/softwaretest"
    assert engineering_root.is_dir()
    assert engineering_root not in runtime_root.parents
