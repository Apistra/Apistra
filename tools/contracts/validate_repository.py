"""Fail-closed CAP-00 repository contract validator with retained fixtures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_FLOW = ["feature/*", "test", "staging", "main"]
AUTOMATIC_DEPLOYMENT_PATTERN = re.compile(r"\b(deploy|deployment)\b", re.IGNORECASE)


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--fixtures", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate_contract(repository_contract(root)) + validate_workflows(root)
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
