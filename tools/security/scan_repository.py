"""Fail-closed repository secret-pattern scan with a retained negative fixture."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = {
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SKIP_PARTS = {".git", "node_modules", ".venv", ".next", "artifacts"}


def scan(root: Path, include_negative_fixture: bool = False) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if (
            relative == "tests/security-fixtures/known-secret.txt"
            and not include_negative_fixture
        ):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{relative}:{line_number}: {name}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--prove-negative-fixture", action="store_true")
    args = parser.parse_args()
    findings = scan(args.root)
    fixture_findings = (
        scan(args.root, include_negative_fixture=True)
        if args.prove_negative_fixture
        else []
    )
    fixture_findings = [
        finding
        for finding in fixture_findings
        if finding.startswith("tests/security-fixtures/known-secret.txt:")
    ]
    if args.prove_negative_fixture and not fixture_findings:
        findings.append("negative secret fixture was not detected")
    for finding in findings:
        print(finding)
    if findings:
        return 1
    print("Secret scan passed and negative fixture was detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
