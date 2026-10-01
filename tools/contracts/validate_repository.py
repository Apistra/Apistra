"""Fail-closed CAP-00 repository contract validator with retained fixtures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath

EXPECTED_FLOW = ["feature/*", "test", "staging", "main"]
EXPECTED_REQUIRED_CHECKS = [
    "Contract and static checks",
    "Architecture",
    "Tests",
    "Security and supply chain",
    "Package candidate",
]
AUTOMATIC_DEPLOYMENT_PATTERN = re.compile(r"\b(deploy|deployment)\b", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RELEASE_VERSION_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:alpha|beta|rc)\.(0|[1-9]\d*))?$"
)
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
    "## Context and current behavior",
    "## Target result",
    "## Prerequisites",
    "## Scope",
    "## Non-goals and prohibited side effects",
    "## Allowed changes",
    "## Stop conditions",
    "## Technical guardrails",
    "## ARCH rules and pattern limits",
    "## SEC rules and safe test conditions",
    "## Acceptance criteria",
    "## Acceptance examples and test oracles",
    "## Expectation sources and independent review",
    "## Required tests",
    "## BDD and manual tests",
    "## Softwaretest.it and CI reporting",
    "## CI retry and evidence reuse",
    "## Deployment and staging evidence",
    "## Documentation and evidence",
    "## Definition of Done",
    "## Workorder completion versus capability acceptance",
    "## Events, rework, and cost",
    "## Dependencies and follow-up",
}
WORKORDER_DELIVERY_CLASSES = {
    "architecture-decision",
    "capability-acceptance",
    "contract-definition",
    "design-decision",
    "implementation",
    "legal-governance",
    "operational-governance",
    "repository-governance",
    "test-definition-and-publication",
}
WORKORDER_FORBIDDEN_BOILERPLATE = {
    "Implement or specify exactly:",
    "The named result is exposed only through the declared application/public contract",
    "unit/component tests for rules, boundaries, state, and error taxonomy",
}
TEST_CONCEPT_REQUIRED_SECTIONS = {
    "## 1. Control summary",
    "## 5. Test organisation and responsibilities",
    "## 7. Test levels and ownership",
    "## 12. Entry criteria",
    "## 13. Exit and gate criteria",
    "## 15. Defect and deviation management",
    "## 20. Evidence and reporting",
    "## 23. Current CAP-00 application",
}
VALID_WORKORDER_STATUSES = {"DRAFT", "BLOCKED", "READY", "DONE"}
PLACEHOLDER_ALLOWED_PATH = (
    "No implementation path is authorised while this workorder is DRAFT/BLOCKED."
)
PROHIBITED_TEST_ALIASES = ("BDD-CAP-", "BDD-WO-", "MT-CAP-")
BDD_ID_PATTERN = re.compile(r"\bBDD-[A-Z]+-\d{3}\b")
MTP_ID_PATTERN = re.compile(r"\bMTP-PRC-\d{2}\b")
MT_ID_PATTERN = re.compile(r"\bMT-PRC-\d{2}-\d{3}\b")
WORKORDER_ID_PATTERN = re.compile(r"\bWO-CAP-\d{2}-\d{2}\b")
MANUAL_CASE_REQUIRED_SECTIONS = {
    "## Objective",
    "## Preconditions",
    "## Procedure",
    "## Cleanup",
    "## Required evidence and oracle",
}
BUSINESS_PATH_AUTHORITY = (
    "Path authority: [Business Workorder Repository Path Contract]"
    "(../../planning/12-repository-path-contract.md)."
)
BUSINESS_PATH_OBSERVATION = "Repository observation: 2026-09-30 at commit `be7e84d`."
ALLOWED_REPOSITORY_PATH_ROOTS = {
    ".github",
    "apps",
    "artifacts",
    "backend",
    "connector-sdk",
    "contracts",
    "deploy",
    "docs",
    "engineering",
    "images",
    "LICENSES",
    "plugin-sdk",
    "tests",
    "tools",
}
WORKORDER_VERSION_PATTERN = re.compile(
    r"^Version: (0\.\d+(?:-(?:draft|ready|done))?)$", re.MULTILINE
)
ALLOWED_REPOSITORY_ROOT_FILES = {
    "CHANGELOG.md",
    "COMMERCIAL-LICENSE.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "LICENSE-TRANSITION.md",
    "NOTICE",
    "SECURITY.md",
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


def validate_branch_policy(policy: dict[str, object]) -> list[str]:
    errors: list[str] = []
    branches = policy.get("branches")
    if not isinstance(branches, dict):
        return ["branch-protection policy must define branches"]
    for branch_name in ("test", "staging", "main"):
        branch = branches.get(branch_name)
        if not isinstance(branch, dict):
            errors.append(f"branch-protection policy must define {branch_name}")
            continue
        expected_values = {
            "pull_requests_required": True,
            "pull_request_reviews": 0,
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "require_conversation_resolution": True,
            "strict_status_checks": True,
            "enforce_admins": True,
            "required_linear_history": True,
            "allow_force_pushes": False,
            "allow_deletions": False,
        }
        for field, expected in expected_values.items():
            if branch.get(field) != expected:
                errors.append(
                    f"{branch_name} branch protection requires {field}={expected!r}"
                )
        if branch.get("required_checks") != EXPECTED_REQUIRED_CHECKS:
            errors.append(
                f"{branch_name} required checks must be {EXPECTED_REQUIRED_CHECKS!r}"
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


def validate_version_values(
    version: str, backend_version: str, web_version: str
) -> list[str]:
    errors: list[str] = []
    if not RELEASE_VERSION_PATTERN.fullmatch(version):
        errors.append("VERSION must contain supported SemVer without build metadata")
    if backend_version != version:
        errors.append("backend/pyproject.toml version must match VERSION")
    if web_version != version:
        errors.append("apps/web/package.json version must match VERSION")
    return errors


def validate_version_policy(root: Path) -> list[str]:
    errors: list[str] = []
    version = (root / "VERSION").read_text(encoding="utf-8").strip()

    backend_text = (root / "backend/pyproject.toml").read_text(encoding="utf-8")
    backend_match = re.search(r'^version\s*=\s*"([^"]+)"', backend_text, re.MULTILINE)
    if backend_match is None:
        errors.append("backend/pyproject.toml must declare a project version")

    web_package = json.loads(
        (root / "apps/web/package.json").read_text(encoding="utf-8")
    )
    errors.extend(
        validate_version_values(
            version,
            backend_match.group(1) if backend_match else "",
            str(web_package.get("version", "")),
        )
    )

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if "## [Unreleased]" not in changelog:
        errors.append("CHANGELOG.md must contain an Unreleased section")
    if not (root / "VERSIONING.md").is_file():
        errors.append("VERSIONING.md must define the version policy")
    return errors


def validate_test_concept(root: Path) -> list[str]:
    path = root / "docs/testing/test-concept.md"
    text = path.read_text(encoding="utf-8")
    missing = _missing_sections(text, TEST_CONCEPT_REQUIRED_SECTIONS)
    if missing:
        return [f"{path}: missing sections: {', '.join(missing)}"]
    return []


def _missing_sections(text: str, required: set[str]) -> list[str]:
    return sorted(section for section in required if section not in text)


def _workorder_delivery_class(text: str) -> str | None:
    match = re.search(r"^- Delivery class: ([a-z-]+)$", text, re.MULTILINE)
    return match.group(1) if match else None


def _rule_ids(text: str, heading: str, prefix: str) -> set[str]:
    section = text.split(heading, 1)
    if len(section) != 2:
        return set()
    section_text = section[1].split("\n## ", 1)[0]
    match = re.search(r"^- Rules: (.+)$", section_text, re.MULTILINE)
    if match is None:
        return set()
    return set(re.findall(rf"\b{prefix}-\d{{3}}\b", match.group(1)))


def _required_workorders(text: str) -> set[str]:
    match = re.search(r"^- Required workorders: (.+)$", text, re.MULTILINE)
    if match is None or match.group(1) == "none within this capability":
        return set()
    return set(WORKORDER_ID_PATTERN.findall(match.group(1)))


def _dependency_cycles(graph: dict[str, set[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(workorder_id: str) -> None:
        if workorder_id in visiting:
            cycles.add(workorder_id)
            return
        if workorder_id in visited:
            return
        visiting.add(workorder_id)
        for dependency in sorted(graph.get(workorder_id, set())):
            if dependency in graph:
                visit(dependency)
        visiting.remove(workorder_id)
        visited.add(workorder_id)

    for workorder_id in sorted(graph):
        visit(workorder_id)
    return cycles


def validate_business_path_contract(
    path: Path, workorder_id: str, text: str
) -> list[str]:
    if workorder_id.startswith("WO-CAP-00-"):
        return []

    errors: list[str] = []
    repository_root = path.resolve().parents[3]
    allowed_section = text.split("## Allowed changes", 1)[-1].split(
        "## Stop conditions", 1
    )[0]

    if PLACEHOLDER_ALLOWED_PATH in allowed_section:
        errors.append(f"{path}: business workorder still has placeholder paths")
    for required in (
        BUSINESS_PATH_AUTHORITY,
        BUSINESS_PATH_OBSERVATION,
        "Observed existing paths within the bounded change area:",
        "Planned additions to the bounded change area after READY:",
        "Workorder-class boundary:",
        "Architecture path gate:",
        "Path boundary:",
    ):
        if required not in allowed_section:
            errors.append(f"{path}: missing business path contract field: {required}")

    existing_paths = re.findall(
        r"^- EXISTING: `([^`]+)`$", allowed_section, re.MULTILINE
    )
    planned_paths = re.findall(r"^- PLANNED: `([^`]+)`$", allowed_section, re.MULTILINE)
    if not existing_paths:
        errors.append(f"{path}: business workorder must list observed EXISTING paths")
    all_paths = existing_paths + planned_paths
    if len(all_paths) != len(set(all_paths)):
        errors.append(f"{path}: repository path entries must be unique")

    for relative in all_paths:
        parsed = PurePosixPath(relative.rstrip("/"))
        if (
            parsed.is_absolute()
            or ".." in parsed.parts
            or "\\" in relative
            or any(character in relative for character in "*?[]{}")
        ):
            errors.append(
                f"{path}: repository path must be literal and relative: {relative}"
            )
            continue
        first = parsed.parts[0] if parsed.parts else ""
        if (
            first not in ALLOWED_REPOSITORY_PATH_ROOTS
            and relative not in ALLOWED_REPOSITORY_ROOT_FILES
        ):
            errors.append(
                f"{path}: repository path is outside approved roots: {relative}"
            )

    for relative in existing_paths:
        if relative == "artifacts/" or relative.startswith("artifacts/"):
            errors.append(
                f"{path}: generated artifact path cannot be observed EXISTING: {relative}"
            )
            continue
        observed = repository_root / relative.rstrip("/")
        if not observed.exists():
            errors.append(f"{path}: observed EXISTING path does not exist: {relative}")

    if workorder_id.startswith("WO-CAP-16-") and (
        "Architecture path gate: BLOCKING" not in allowed_section
        or "`contracts/plugins/`" not in allowed_section
        or "`plugin-sdk/python/`" not in allowed_section
    ):
        errors.append(
            f"{path}: CAP-16 must retain the plugin-root architecture blocker"
        )
    if workorder_id.startswith("WO-CAP-17-") and (
        "Architecture path gate: BLOCKING" not in allowed_section
        or "`deploy/kubernetes/`" not in allowed_section
    ):
        errors.append(
            f"{path}: CAP-17 must retain the Kubernetes-root architecture blocker"
        )
    return errors


def validate_workorder_contract(
    path: Path,
    workorder_id: str,
    text: str,
    canonical_bdd_ids: set[str],
    canonical_mtp_ids: set[str],
    defined_arch_ids: set[str],
    defined_sec_ids: set[str],
) -> tuple[list[str], str | None, set[str]]:
    errors: list[str] = []
    if re.search(r"^## Stop conditions\S", text, re.MULTILINE):
        errors.append(f"{path}: malformed Stop conditions heading")
    version_match = WORKORDER_VERSION_PATTERN.search(text)
    if version_match is None:
        errors.append(f"{path}: workorder contract must use a supported 0.x revision")

    status_match = re.search(r"^Status: (.+)$", text, re.MULTILINE)
    status = status_match.group(1) if status_match else ""
    if status not in VALID_WORKORDER_STATUSES:
        errors.append(
            f"{path}: Status must be exactly one of {sorted(VALID_WORKORDER_STATUSES)}"
        )
    for field in (
        "Status reason",
        "Implementation state",
        "Evidence state",
        "Approval state",
    ):
        if re.search(rf"^{field}: \S.+$", text, re.MULTILINE) is None:
            errors.append(f"{path}: missing separate {field} field")

    delivery_class = _workorder_delivery_class(text)
    if delivery_class not in WORKORDER_DELIVERY_CLASSES:
        errors.append(f"{path}: missing or unsupported delivery class")
    if f"- Owned verification group: TST-{workorder_id}" not in text:
        errors.append(f"{path}: owned verification group must be TST-{workorder_id}")
    version = version_match.group(1) if version_match else ""
    if f"- Specification revision: {version}" not in text:
        errors.append(f"{path}: specification revision must match Version")
    if "- **Positive oracle:**" not in text or "- **Negative oracle:**" not in text:
        errors.append(f"{path}: positive and negative test oracles are mandatory")
    if "- Positive expectation:" not in text or "- Counterexample:" not in text:
        errors.append(f"{path}: independent expectation inputs are mandatory")
    if "- Required workorders:" not in text:
        errors.append(f"{path}: explicit workorder dependencies are mandatory")
    if (
        "- Applicability:"
        not in text.split("## ARCH rules and pattern limits", 1)[-1].split(
            "## SEC rules", 1
        )[0]
    ):
        errors.append(f"{path}: ARCH rule applicability is mandatory")
    if (
        "- Applicability:"
        not in text.split("## SEC rules and safe test conditions", 1)[-1].split(
            "## Acceptance criteria", 1
        )[0]
    ):
        errors.append(f"{path}: SEC rule applicability is mandatory")

    arch_ids = _rule_ids(text, "## ARCH rules and pattern limits", "ARCH")
    sec_ids = _rule_ids(text, "## SEC rules and safe test conditions", "SEC")
    for rule_id in sorted(arch_ids - defined_arch_ids):
        errors.append(f"{path}: undefined architecture rule {rule_id}")
    for rule_id in sorted(sec_ids - defined_sec_ids):
        errors.append(f"{path}: undefined security rule {rule_id}")

    referenced_bdd_ids = set(BDD_ID_PATTERN.findall(text))
    referenced_mtp_ids = set(MTP_ID_PATTERN.findall(text))
    for test_id in sorted(referenced_bdd_ids - canonical_bdd_ids):
        errors.append(f"{path}: undefined canonical behavioural test ID {test_id}")
    for package_id in sorted(referenced_mtp_ids - canonical_mtp_ids):
        errors.append(f"{path}: undefined canonical manual package ID {package_id}")
    for alias in PROHIBITED_TEST_ALIASES:
        if alias in text:
            errors.append(f"{path}: prohibited generated test alias {alias}")
    if re.search(r"\b(?:BDD|MT)-[^\s`,;)]+\*", text):
        errors.append(f"{path}: wildcard test identifiers are prohibited")

    errors.extend(validate_business_path_contract(path, workorder_id, text))

    if status in {"READY", "DONE"}:
        if PLACEHOLDER_ALLOWED_PATH in text:
            errors.append(f"{path}: READY/DONE workorder still has placeholder paths")
        if "NOT ALLOCATED" in text:
            errors.append(f"{path}: READY/DONE workorder has unallocated test IDs")
    for phrase in sorted(WORKORDER_FORBIDDEN_BOILERPLATE):
        if phrase in text:
            errors.append(f"{path}: forbidden generic boilerplate remains: {phrase}")
    return errors, delivery_class, _required_workorders(text)


def validate_manual_test_case(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    test_id = path.stem
    if not text.startswith(f"# {test_id} — "):
        errors.append(f"{path}: heading must start with {test_id}")
    status_match = re.search(r"^Status: (.+)$", text, re.MULTILINE)
    status = status_match.group(1) if status_match else ""
    if status not in {
        "DRAFT; NOT PUBLISHED; NOT EXECUTED",
        "PUBLISHED; NOT EXECUTED",
    }:
        errors.append(
            f"{path}: manual case must declare a supported publication/execution state"
        )
    for section in _missing_sections(text, MANUAL_CASE_REQUIRED_SECTIONS):
        errors.append(f"{path}: missing section {section}")

    step_numbers = [
        int(number)
        for number in re.findall(
            r"^(\d+)\. \*\*(?:Action|Observation) \([^)]+\):\*\* .+$",
            text,
            re.MULTILINE,
        )
    ]
    data_count = len(re.findall(r"^\s+\*\*Test data:\*\* .+$", text, re.MULTILINE))
    expected_count = len(
        re.findall(r"^\s+\*\*Expected result:\*\* .+$", text, re.MULTILINE)
    )
    if not step_numbers:
        errors.append(f"{path}: manual case must contain atomic role-prefixed steps")
    elif step_numbers != list(range(1, len(step_numbers) + 1)):
        errors.append(f"{path}: manual step numbers must be consecutive from 1")
    if data_count != len(step_numbers) or expected_count != len(step_numbers):
        errors.append(
            f"{path}: every manual step must have one test data and expected result"
        )
    if not re.search(
        r"^1\. \*\*Action \((?:Bootstrap visitor|Logged-out visitor)\):\*\* "
        r"Open `STAGING_SIGN_IN_URL`",
        text,
        re.MULTILINE,
    ):
        errors.append(f"{path}: first step must start logged out at sign-in")
    return errors


def validate_manual_test_definitions(root: Path, test_catalog: str) -> list[str]:
    errors: list[str] = []
    manual_root = root / "docs/testing/manual"
    catalogue_ids = set(MT_ID_PATTERN.findall(test_catalog))
    case_files = sorted(manual_root.glob("PRC-*/MT-PRC-??-???.md"))
    file_ids = {path.stem for path in case_files}

    for test_id in sorted(catalogue_ids - file_ids):
        errors.append(f"{manual_root}: allocated manual case {test_id} has no file")
    for test_id in sorted(file_ids - catalogue_ids):
        errors.append(f"{manual_root}: manual case file {test_id} is not allocated")
    for path in case_files:
        errors.extend(validate_manual_test_case(path, path.read_text(encoding="utf-8")))
    return errors


def validate_planning_catalogues(root: Path) -> list[str]:
    errors: list[str] = []
    capabilities = root / "docs/capabilities"
    workorders = root / "docs/workorders"
    capability_index = (capabilities / "README.md").read_text(encoding="utf-8")
    workorder_index = (workorders / "README.md").read_text(encoding="utf-8")
    test_catalog_path = root / "docs/testing/test-id-catalog.md"
    test_catalog = test_catalog_path.read_text(encoding="utf-8")
    canonical_bdd_ids = set(BDD_ID_PATTERN.findall(test_catalog))
    canonical_mtp_ids = set(MTP_ID_PATTERN.findall(test_catalog))
    architecture = (root / "docs/planning/03-architecture.md").read_text(
        encoding="utf-8"
    )
    security = (root / "docs/planning/04-security-concept.md").read_text(
        encoding="utf-8"
    )
    defined_arch_ids = set(re.findall(r"^(ARCH-\d{3}) —", architecture, re.MULTILINE))
    defined_sec_ids = set(re.findall(r"^(SEC-\d{3}) —", security, re.MULTILINE))

    if "Version: 0.7-draft" not in test_catalog or "Status: DRAFT" not in test_catalog:
        errors.append(f"{test_catalog_path}: must declare the 0.7 draft authority")
    if len(canonical_bdd_ids) != 47:
        errors.append(
            f"{test_catalog_path}: expected 47 canonical BDD IDs, observed {len(canonical_bdd_ids)}"
        )
    if canonical_mtp_ids != {f"MTP-PRC-{number:02d}" for number in range(1, 15)}:
        errors.append(
            f"{test_catalog_path}: manual package catalogue must be PRC-01 through PRC-14"
        )
    errors.extend(validate_manual_test_definitions(root, test_catalog))

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
        delivery_classes: list[str] = []
        workorder_dependencies: dict[str, set[str]] = {}
        workorder_classes: dict[str, str] = {}
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
            workorder_errors, delivery_class, dependencies = (
                validate_workorder_contract(
                    workorder_path,
                    workorder_id,
                    workorder_text,
                    canonical_bdd_ids,
                    canonical_mtp_ids,
                    defined_arch_ids,
                    defined_sec_ids,
                )
            )
            errors.extend(workorder_errors)
            if delivery_class is not None:
                delivery_classes.append(delivery_class)
                workorder_classes[workorder_id] = delivery_class
            workorder_dependencies[workorder_id] = dependencies
            if f"{capability_id}/{name}" not in workorder_index:
                errors.append(f"{workorder_path}: missing from workorder index")
            if f"../workorders/{capability_id}/{name}" not in text:
                errors.append(f"{workorder_path}: missing from {path}")

        if delivery_classes.count("test-definition-and-publication") != 1:
            errors.append(
                f"{directory}: capability must own exactly one test-definition-and-publication workorder"
            )
        if delivery_classes.count("capability-acceptance") != 1:
            errors.append(
                f"{directory}: capability must own exactly one capability-acceptance workorder"
            )

        known_workorders = set(workorder_dependencies)
        for workorder_id, dependencies in workorder_dependencies.items():
            if workorder_id in dependencies:
                errors.append(f"{directory}: {workorder_id} depends on itself")
            for dependency in sorted(dependencies - known_workorders):
                errors.append(
                    f"{directory}: {workorder_id} has missing or cross-capability dependency {dependency}"
                )

        for workorder_id in sorted(_dependency_cycles(workorder_dependencies)):
            errors.append(f"{directory}: dependency cycle includes {workorder_id}")

        publication_ids = {
            workorder_id
            for workorder_id, delivery_class in workorder_classes.items()
            if delivery_class == "test-definition-and-publication"
        }
        acceptance_ids = {
            workorder_id
            for workorder_id, delivery_class in workorder_classes.items()
            if delivery_class == "capability-acceptance"
        }
        if len(publication_ids) == 1 and capability_id != "CAP-00":
            publication_id = next(iter(publication_ids))
            for workorder_id, delivery_class in workorder_classes.items():
                if (
                    delivery_class == "implementation"
                    and publication_id not in workorder_dependencies[workorder_id]
                ):
                    errors.append(
                        f"{directory}: implementation {workorder_id} must depend on {publication_id}"
                    )
        if len(acceptance_ids) == 1:
            acceptance_id = next(iter(acceptance_ids))
            expected_dependencies = known_workorders - {acceptance_id}
            if workorder_dependencies[acceptance_id] != expected_dependencies:
                errors.append(
                    f"{directory}: acceptance {acceptance_id} must depend on every other workorder"
                )

    return errors


def validate_local_planning_links(root: Path) -> list[str]:
    errors: list[str] = []
    paths = [
        root / "README.md",
        root / "CHANGELOG.md",
        root / "VERSIONING.md",
        root / "docs/planning/README.md",
        root / "docs/planning/06-test-architecture.md",
        root / "docs/planning/08-capabilities-and-roadmap.md",
        root / "docs/planning/09-workorders.md",
        root / "docs/testing/test-concept.md",
        root / "docs/testing/test-id-catalog.md",
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
        + validate_branch_policy(
            json.loads((root / ".github/branch-protection.expected.json").read_text())
        )
        + validate_workflows(root)
        + validate_version_policy(root)
        + validate_test_concept(root)
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
        if validate_version_values("0.1.0", "0.1.0", "0.1.0"):
            errors.append("positive version fixture must pass")
        if not validate_version_values("0.1.0+local", "0.1.0", "0.2.0"):
            errors.append("negative version fixture must fail")
        catalogue_text = (root / "docs/testing/test-id-catalog.md").read_text(
            encoding="utf-8"
        )
        architecture_text = (root / "docs/planning/03-architecture.md").read_text(
            encoding="utf-8"
        )
        security_text = (root / "docs/planning/04-security-concept.md").read_text(
            encoding="utf-8"
        )
        fixture_path = root / "docs/workorders/CAP-01/WO-CAP-01-01.md"
        fixture_text = fixture_path.read_text(encoding="utf-8")
        fixture_args = (
            fixture_path,
            "WO-CAP-01-01",
            set(BDD_ID_PATTERN.findall(catalogue_text)),
            set(MTP_ID_PATTERN.findall(catalogue_text)),
            set(re.findall(r"^(ARCH-\d{3}) —", architecture_text, re.MULTILINE)),
            set(re.findall(r"^(SEC-\d{3}) —", security_text, re.MULTILINE)),
        )
        fixture_errors, _, _ = validate_workorder_contract(
            fixture_args[0], fixture_args[1], fixture_text, *fixture_args[2:]
        )
        if fixture_errors:
            errors.append("positive workorder contract fixture must pass")
        invalid_workorder = re.sub(
            r"^Status: .+$",
            "Status: PLANNED",
            fixture_text,
            count=1,
            flags=re.MULTILINE,
        ).replace("BDD-AUTH-001", "BDD-CAP-01-01")
        invalid_errors, _, _ = validate_workorder_contract(
            fixture_args[0], fixture_args[1], invalid_workorder, *fixture_args[2:]
        )
        if not any("Status must be exactly" in error for error in invalid_errors):
            errors.append("negative workorder status fixture must fail")
        if not any(
            "prohibited generated test alias" in error for error in invalid_errors
        ):
            errors.append("negative workorder test-ID fixture must fail")
        invalid_path_workorder = re.sub(
            r"^- EXISTING: `[^`]+`$",
            "- EXISTING: `missing/path/`",
            fixture_text,
            count=1,
            flags=re.MULTILINE,
        )
        invalid_path_errors, _, _ = validate_workorder_contract(
            fixture_args[0], fixture_args[1], invalid_path_workorder, *fixture_args[2:]
        )
        if not any(
            "observed EXISTING path does not exist" in error
            for error in invalid_path_errors
        ):
            errors.append("negative business path fixture must fail")
        manual_path = root / "docs/testing/manual/PRC-01/MT-PRC-01-001.md"
        manual_text = manual_path.read_text(encoding="utf-8")
        if validate_manual_test_case(manual_path, manual_text):
            errors.append("positive manual test definition fixture must pass")
        invalid_manual = manual_text.replace("**Expected result:**", "**Result:**", 1)
        invalid_manual_errors = validate_manual_test_case(manual_path, invalid_manual)
        if not any(
            "every manual step must have one test data and expected result" in error
            for error in invalid_manual_errors
        ):
            errors.append("negative manual test definition fixture must fail")
    for error in errors:
        print(error)
    if errors:
        return 1
    print("Repository contract and proof fixtures passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
