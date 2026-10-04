from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BDD_IDS = (
    "BDD-SECRET-001",
    "BDD-ENDPOINT-001",
    "BDD-AGENT-001",
    "BDD-TOOL-001",
    "BDD-LIMIT-001",
)
MANUAL_IDS = tuple(f"MT-PRC-01-{index:03d}" for index in range(7, 15))


def test_cap02_bdd_definitions_are_present_and_stably_tagged() -> None:
    feature = ROOT / "tests/bdd/features/cap_02/configuration.feature"
    text = feature.read_text(encoding="utf-8")
    for stable_id in BDD_IDS:
        assert text.count(f"@{stable_id}") == 1
    assert "Feature:" in text
    assert "Given " in text
    assert "When " in text
    assert "Then " in text


def test_cap02_manual_package_is_complete_and_independently_executable() -> None:
    directory = ROOT / "docs/testing/manual/PRC-01/CAP-02"
    case_files = sorted(directory.glob("MT-PRC-01-*.md"))
    assert [path.stem for path in case_files] == list(MANUAL_IDS)
    for path in case_files:
        text = path.read_text(encoding="utf-8")
        assert "Status: DRAFT; NOT PUBLISHED; NOT EXECUTED" in text
        assert "STAGING_SIGN_IN_URL" in text
        assert "**Action (Logged-out visitor):**" in text
        assert "## Cleanup" in text
        assert "## Required evidence and oracle" in text


def test_cap02_review_and_design_gates_remain_scoped_after_publication() -> None:
    review = (ROOT / "docs/planning/14-cap02-readiness-review.md").read_text(encoding="utf-8")
    design = (ROOT / "docs/planning/07-design-contract.md").read_text(encoding="utf-8")
    assert "Status: IMPLEMENTATION ACTIVE; WO-CAP-02-06 DONE" in review
    assert "Status: APPROVED." in design
    assert "not capability acceptance" in review.lower()
    assert "not implementation" in design.lower()


def test_cap02_publication_workorder_is_done_and_retains_path_ownership() -> None:
    workorder = (ROOT / "docs/workorders/CAP-02/WO-CAP-02-06.md").read_text(encoding="utf-8")
    assert "Status: DONE" in workorder
    assert "protected run 37212285531" in workorder
    for path in (
        "docs/testing/manual/PRC-01/CAP-02/",
        "tests/bdd/features/cap_02/",
        "tools/fixtures/cap_02/",
        "backend/tests/contract/",
        "tools/contracts/validate_repository.py",
        ".github/workflows/ci.yml",
    ):
        assert f"`{path}`" in workorder
