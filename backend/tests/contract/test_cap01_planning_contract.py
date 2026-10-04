from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_cap01_bdd_definitions_are_present_and_stably_tagged() -> None:
    feature = ROOT / "tests/bdd/features/cap_01/administration.feature"
    text = feature.read_text(encoding="utf-8")
    assert text.count("@BDD-AUTH-001") == 1
    assert text.count("@BDD-PROJ-001") == 1
    assert "Feature:" in text
    assert "Given " in text
    assert "When " in text
    assert "Then " in text


def test_cap01_readiness_review_records_verified_publication_gate() -> None:
    review = ROOT / "docs/planning/13-cap01-readiness-review.md"
    text = review.read_text(encoding="utf-8")
    assert "APPROVED; EXTERNAL PUBLISHING GATE CLOSED" in text
    assert "APISTRA-TC-000002" in text
    assert "APISTRA-TC-000007" in text
    assert "created zero execution results" in text
    assert "No staging execution" in text


def test_cap01_workorders_have_specific_pattern_mappings() -> None:
    expected = {
        "WO-CAP-01-01.md": (
            "ADR-001, ADR-002, ADR-003, ADR-004, ADR-013, ADR-017, ADR-018, ADR-019, ADR-021"
        ),
        "WO-CAP-01-02.md": "ADR-001, ADR-003, ADR-004, ADR-013, ADR-014, ADR-017, ADR-018, ADR-019",
        "WO-CAP-01-03.md": (
            "ADR-001, ADR-002, ADR-003, ADR-004, ADR-013, ADR-017, ADR-018, ADR-019, ADR-021"
        ),
        "WO-CAP-01-04.md": "ADR-002, ADR-010, ADR-013, ADR-017, ADR-018, ADR-019",
    }
    directory = ROOT / "docs/workorders/CAP-01"
    for filename, mapping in expected.items():
        text = directory.joinpath(filename).read_text(encoding="utf-8")
        assert f"- ADRs/patterns: {mapping}" in text
        assert "ADR-001 through ADR-005" not in text

    acceptance = directory.joinpath("WO-CAP-01-05.md").read_text(encoding="utf-8")
    assert "introduces no new implementation pattern" in acceptance


def test_design_approvals_remain_capability_scoped_not_global() -> None:
    design = (ROOT / "docs/planning/07-design-contract.md").read_text(encoding="utf-8")
    normalized = " ".join(design.split())
    assert "Approval boundary for revision 0.3" in design
    assert "approved this exact revision on 2026-09-30 for DSN-001 through DSN-004" in normalized
    assert "CAP-02 approval is granted separately" in normalized
    assert "Status: APPROVED." in design
    assert "pending elsewhere" in design
