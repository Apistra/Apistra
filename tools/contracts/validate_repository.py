"""Fail-closed CAP-00 repository contract validator with retained fixtures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_FLOW = ["feature/*", "test", "staging", "main"]
AUTOMATIC_DEPLOYMENT_PATTERN = re.compile(r"\b(deploy|deployment)\b", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXPECTED_WORKORDER_COUNTS = {
    "CAP-00": 7,
    "CAP-01": 5,
    "CAP-02": 7,
    "CAP-03": 7,
    "CAP-04": 8,
    "CAP-05": 9,
    "CAP-06": 10,
    "CAP-07": 7,
    "CAP-08": 8,
    "CAP-09": 6,
    "CAP-10": 8,
    "CAP-11": 7,
    "CAP-12": 6,
    "CAP-13": 7,
    "CAP-14": 6,
    "CAP-15": 8,
    "CAP-16": 8,
    "CAP-17": 7,
    "CAP-18": 9,
}
CAPABILITY_REQUIRED_SECTIONS = {
    "## Control summary",
    "## Goal and value",
    "## Traceability",
    "## Scope",
    "## Non-goals",
    "## Binding rules",
    "## Acceptance criteria",
    "## Test and evidence contract",
    "## Workorders",
    "## Staging and gate",
    "## Open decisions",
}
WORKORDER_REQUIRED_SECTIONS = {
    "## Status and traceability",
    "## Risk profile and escalation",
    "## Baselines and contract delta",
    "## Target result",
    "## Prerequisites",
    "## Scope",
    "## Non-goals and prohibited side effects",
    "## Stop conditions",
    "## ARCH rules and pattern limits",
    "## SEC rules and safe test conditions",
    "## Acceptance criteria",
    "## Required tests",
    "## Softwaretest.it and CI reporting",
    "## Deployment and staging evidence",
    "## Definition of Done",
}


def validate_contract(contract: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if contract.get("flow") != EXPECTED_FLOW:
        errors.append(f"branch flow must be {EXPECTED_FLOW!r}")
    if contract.get("automatic_deployment") is not False:
        errors.append("automatic deployment must be false")
    if contract.get("external_contributions") is not False:
        errors.append(
            "external contributions must remain disabled during 0.x foundation"
        )
    return errors


def repository_contract(root: Path) -> dict[str, object]:
    policy = json.loads((root / ".github/branch-protection.expected.json").read_text())
    contributing = (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    return {
        "flow": policy["flow"],
        "automatic_deployment": policy["deployment"]["automatic"],
        "external_contributions": "external code contributions are not accepted"
        not in contributing,
    }


def validate_workflows(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            if (
                AUTOMATIC_DEPLOYMENT_PATTERN.search(line)
                and "manual" not in line.lower()
            ):
                errors.append(
                    f"{path}:{line_number}: workflow contains deployment language"
                )
    return errors


def _missing_sections(text: str, required: set[str]) -> list[str]:
    return sorted(section for section in required if section not in text)


def validate_planning_catalogues(root: Path) -> list[str]:
    errors: list[str] = []
    capabilities = root / "docs/capabilities"
    workorders = root / "docs/workorders"
    capability_index = (capabilities / "README.md").read_text(encoding="utf-8")
    workorder_index = (workorders / "README.md").read_text(encoding="utf-8")

    capability_files = sorted(capabilities.glob("CAP-*.md"))
    observed_capability_ids = [path.name[:6] for path in capability_files]
    expected_capability_ids = list(EXPECTED_WORKORDER_COUNTS)
    if observed_capability_ids != expected_capability_ids:
        errors.append(
            "capability files must contain exactly CAP-00 through CAP-18 in order"
        )

    for capability_id in expected_capability_ids:
        matches = sorted(capabilities.glob(f"{capability_id}-*.md"))
        if len(matches) != 1:
            errors.append(
                f"{capability_id} must have exactly one canonical capability file"
            )
            continue
        path = matches[0]
        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# {capability_id} — "):
            errors.append(f"{path}: heading must start with {capability_id}")
        missing = _missing_sections(text, CAPABILITY_REQUIRED_SECTIONS)
        if missing:
            errors.append(f"{path}: missing sections: {', '.join(missing)}")
        if path.name not in capability_index:
            errors.append(f"{path}: missing from capability index")

        expected_names = [
            f"WO-{capability_id}-{number:02d}.md"
            for number in range(1, EXPECTED_WORKORDER_COUNTS[capability_id] + 1)
        ]
        directory = workorders / capability_id
        observed_names = sorted(path.name for path in directory.glob("WO-*.md"))
        if observed_names != expected_names:
            errors.append(
                f"{directory}: expected {expected_names!r}, observed {observed_names!r}"
            )
        for name in expected_names:
            workorder_path = directory / name
            if not workorder_path.is_file():
                continue
            workorder_text = workorder_path.read_text(encoding="utf-8")
            workorder_id = name.removesuffix(".md")
            if not workorder_text.startswith(f"# {workorder_id} — "):
                errors.append(
                    f"{workorder_path}: heading must start with {workorder_id}"
                )
            missing = _missing_sections(workorder_text, WORKORDER_REQUIRED_SECTIONS)
            if missing:
                errors.append(
                    f"{workorder_path}: missing sections: {', '.join(missing)}"
                )
            if f"{capability_id}/{name}" not in workorder_index:
                errors.append(f"{workorder_path}: missing from workorder index")
            if f"../workorders/{capability_id}/{name}" not in text:
                errors.append(f"{workorder_path}: missing from {path}")

    return errors


def validate_local_planning_links(root: Path) -> list[str]:
    errors: list[str] = []
    paths = [
        root / "README.md",
        root / "docs/planning/README.md",
        root / "docs/planning/08-capabilities-and-roadmap.md",
        root / "docs/planning/09-workorders.md",
        *(root / "docs/capabilities").glob("*.md"),
        *(root / "docs/workorders").glob("**/*.md"),
    ]
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_PATTERN.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            relative_target = target.split("#", 1)[0]
            if not (path.parent / relative_target).resolve().exists():
                errors.append(f"{path}: broken local link: {target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--fixtures", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = (
        validate_contract(repository_contract(root))
        + validate_workflows(root)
        + validate_planning_catalogues(root)
        + validate_local_planning_links(root)
    )
    if args.fixtures:
        positive = json.loads(
            (
                root / "tests/contract-fixtures/positive/repository-contract.json"
            ).read_text()
        )
        negative = json.loads(
            (
                root / "tests/contract-fixtures/negative/repository-contract.json"
            ).read_text()
        )
        if validate_contract(positive):
            errors.append("positive contract fixture must pass")
        if not validate_contract(negative):
            errors.append("negative contract fixture must fail")
    for error in errors:
        print(error)
    if errors:
        return 1
    print("Repository contract and proof fixtures passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
