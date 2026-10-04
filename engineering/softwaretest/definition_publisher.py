"""Publish reviewed capability manual definitions with verified readback.

The default mode is local-only and writes a lossless outbox. ``--apply`` is
required for any remote mutation. The publisher never creates executions or
test results.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from publisher import ApiError, payload_sha256, redact, request_json, write_json_atomic

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_DIR = ROOT / "docs/testing/manual/PRC-01"
DEFAULT_OUTBOX = ROOT / "artifacts/softwaretest-cap01-definition-outbox.json"
DEFAULT_RECEIPT = ROOT / "artifacts/softwaretest-cap01-definition-receipt.json"
CAP02_MANUAL_DIR = DEFAULT_MANUAL_DIR / "CAP-02"
CAP02_OUTBOX = ROOT / "artifacts/softwaretest-cap02-definition-outbox.json"
CAP02_RECEIPT = ROOT / "artifacts/softwaretest-cap02-definition-receipt.json"
CASE_PATTERN = re.compile(r"MT-PRC-01-\d{3}")
STEP_PATTERN = re.compile(r"^(\d+)\. \*\*(Action|Observation) \(([^)]+)\):\*\* (.+)$")
FIELD_NAME = "name"
FIELD_BUILD = "build"
FIELD_ENVIRONMENT = "environment"
FIELD_ACTION = "action"
FIELD_TEST_DATA = "test_data"
FIELD_EXPECTED = "expected"
FIELD_STABLE_ID = "stable_id"
FIELD_TITLE = "title"
FIELD_PRECONDITIONS = "preconditions"
FIELD_STEPS = "steps"
FIELD_DESCRIPTION = "description"
FIELD_PRIORITY = "priority"
FIELD_ESTIMATED_MINUTES = "estimated_minutes"
FIELD_PAYLOAD = "payload"
FIELD_DEFINITIONS = "definitions"
FIELD_MANIFEST_SHA256 = "manifest_sha256"
FIELD_STATUS = "status"
FIELD_ID = "id"
FIELD_VERIFIED = "verified"
FIELD_CAPABILITY = "capability"
HTTP_POST = "POST"
CAP02_CASE_STOP = 15
Requester = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class PackageConfig:
    """Immutable local publishing contract for one capability package."""

    capability: str
    workorder: str
    manual_dir: Path
    outbox: Path
    receipt: Path
    expected_ids: tuple[str, ...]
    cycle: dict[str, str]
    command_revision: str

    @property
    def key_namespace(self) -> str:
        return self.capability.lower().replace("-", "")


CAP01_PACKAGE = PackageConfig(
    capability="CAP-01",
    workorder="WO-CAP-01-04",
    manual_dir=DEFAULT_MANUAL_DIR,
    outbox=DEFAULT_OUTBOX,
    receipt=DEFAULT_RECEIPT,
    expected_ids=tuple(f"MT-PRC-01-{index:03d}" for index in range(1, 7)),
    cycle={
        FIELD_NAME: "Apistra CAP-01 Acceptance",
        "objective": (
            "Publish and later execute the approved CAP-01 administration and "
            "project-isolation acceptance package."
        ),
        FIELD_BUILD: "CAP-01",
        FIELD_ENVIRONMENT: "isolated-local-staging",
    },
    command_revision="cap01-definitions-v1",
)
CAP02_PACKAGE = PackageConfig(
    capability="CAP-02",
    workorder="WO-CAP-02-06",
    manual_dir=CAP02_MANUAL_DIR,
    outbox=CAP02_OUTBOX,
    receipt=CAP02_RECEIPT,
    expected_ids=tuple(f"MT-PRC-01-{index:03d}" for index in range(7, CAP02_CASE_STOP)),
    cycle={
        FIELD_NAME: "Apistra CAP-02 Acceptance",
        "objective": (
            "Publish and later execute the approved CAP-02 safe AI "
            "configuration acceptance package."
        ),
        FIELD_BUILD: "CAP-02",
        FIELD_ENVIRONMENT: "isolated-local-staging",
    },
    command_revision="cap02-definitions-v1",
)
PACKAGES = {package.capability: package for package in (CAP01_PACKAGE, CAP02_PACKAGE)}
CYCLE = CAP01_PACKAGE.cycle


def stable_key(command: str, value: str, namespace: str = "cap01") -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:24]
    return f"apistra-{namespace}-{command}-{digest}"


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    start_marker = f"## {heading}\n"
    if start_marker not in text:
        raise ValueError(f"missing section: {heading}")
    body = text.split(start_marker, 1)[1]
    if next_heading:
        end_marker = f"\n## {next_heading}"
        if end_marker not in body:
            raise ValueError(f"missing section after {heading}: {next_heading}")
        body = body.split(end_marker, 1)[0]
    return body.strip()


def _metadata(text: str, name: str, *, required: bool = True) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    if required:
        raise ValueError(f"missing metadata: {name}")
    return ""


def _plain_heading(text: str) -> tuple[str, str]:
    first = text.splitlines()[0]
    match = re.fullmatch(r"# (MT-PRC-01-\d{3}) — (.+)", first)
    if not match:
        raise ValueError("manual case heading must contain a stable MT-PRC-01 ID")
    return match.group(1), match.group(2)


def _normalise_markdown_lines(value: str) -> str:
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def _new_step(line: str) -> dict[str, str] | None:
    match = STEP_PATTERN.match(line)
    if not match:
        return None
    number, kind, role, action = match.groups()
    return {
        "number": number,
        FIELD_ACTION: f"{role}: {action}",
        FIELD_TEST_DATA: "",
        FIELD_EXPECTED: "",
        "kind": kind,
    }


def _step_field(line: str) -> tuple[str, str] | None:
    fields = {
        "**Test data:**": FIELD_TEST_DATA,
        "**Expected result:**": FIELD_EXPECTED,
    }
    for prefix, field in fields.items():
        if line.startswith(prefix):
            return field, line.removeprefix(prefix).strip()
    return None


def _validate_steps(steps: list[dict[str, str]]) -> None:
    if not steps:
        raise ValueError("manual case has no procedure steps")
    for index, step in enumerate(steps, 1):
        if int(step.pop("number")) != index:
            raise ValueError("manual steps must be consecutively numbered")
        step.pop("kind")
        if not step[FIELD_ACTION] or not step[FIELD_EXPECTED]:
            raise ValueError(f"step {index} has no action or expected result")


def _parse_steps(text: str) -> list[dict[str, str]]:
    procedure = _section(text, "Procedure", "Cleanup")
    steps: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    active_field = ""
    for raw_line in procedure.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        new_step = _new_step(line)
        if new_step:
            if current:
                steps.append(current)
            current = new_step
            active_field = FIELD_ACTION
            continue
        if current is None:
            raise ValueError("content found before the first procedure step")
        field = _step_field(line)
        if field:
            field_name, value = field
            current[field_name] = value
            active_field = field_name
        elif active_field:
            current[active_field] = f"{current[active_field]} {line}".strip()
    if current:
        steps.append(current)
    _validate_steps(steps)
    return steps


def parse_case(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stable_id, title = _plain_heading(text)
    if path.stem != stable_id:
        raise ValueError(f"filename and stable ID differ: {path.name}")
    objective = _normalise_markdown_lines(_section(text, "Objective", "Preconditions"))
    preconditions = _section(text, "Preconditions", "Procedure")
    traceability = {
        "version": _metadata(text, "Version"),
        "actor": _metadata(text, "Actor"),
        "fixture": _metadata(text, "Fixture"),
        "requirements": _metadata(text, "Requirement links"),
        "risks": _metadata(text, "Risk links"),
        "bdd": _metadata(text, "BDD link"),
        "design": _metadata(text, "Design links", required=False),
    }
    steps = _parse_steps(text)
    source_sha256 = payload_sha256(
        {
            FIELD_STABLE_ID: stable_id,
            FIELD_TITLE: title,
            "objective": objective,
            FIELD_PRECONDITIONS: preconditions,
            "traceability": traceability,
            FIELD_STEPS: steps,
        }
    )
    description_lines = [
        objective,
        "",
        f"Stable ID: {stable_id}",
        f"Source version: {traceability['version']}",
        f"Source SHA-256: {source_sha256}",
        f"Actor: {traceability['actor']}",
        f"Fixture: {traceability['fixture']}",
        f"Requirements: {traceability['requirements']}",
        f"Risks: {traceability['risks']}",
        f"BDD: {traceability['bdd']}",
    ]
    if traceability["design"]:
        description_lines.append(f"Design: {traceability['design']}")
    payload = {
        FIELD_TITLE: f"[{stable_id}] {title}",
        FIELD_DESCRIPTION: "\n".join(description_lines),
        FIELD_PRECONDITIONS: preconditions,
        FIELD_PRIORITY: "HIGH",
        FIELD_ESTIMATED_MINUTES: 20,
        FIELD_STEPS: steps,
    }
    return {
        FIELD_STABLE_ID: stable_id,
        "source_path": path.relative_to(ROOT).as_posix(),
        "source_sha256": source_sha256,
        "payload_sha256": payload_sha256(payload),
        FIELD_PAYLOAD: payload,
        "traceability": traceability,
    }


def build_manifest(
    manual_dir: Path | None = None,
    package: PackageConfig = CAP01_PACKAGE,
) -> dict[str, Any]:
    source_dir = manual_dir or package.manual_dir
    definitions = [parse_case(path) for path in sorted(source_dir.glob("MT-*.md"))]
    manifest = {
        "schema_version": "1.0",
        FIELD_CAPABILITY: package.capability,
        "process": "PRC-01",
        "workorder": package.workorder,
        "cycle": package.cycle,
        FIELD_DEFINITIONS: definitions,
    }
    validate_manifest(manifest, package)
    manifest[FIELD_MANIFEST_SHA256] = payload_sha256(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any], package: PackageConfig) -> None:
    definitions = manifest.get(FIELD_DEFINITIONS, [])
    stable_ids = [definition[FIELD_STABLE_ID] for definition in definitions]
    if tuple(stable_ids) != package.expected_ids:
        raise ValueError(
            f"{package.capability} package must contain exactly "
            f"{', '.join(package.expected_ids)}"
        )
    if len(set(stable_ids)) != len(stable_ids):
        raise ValueError("manual definition IDs must be unique")
    for definition in definitions:
        stable_id = definition[FIELD_STABLE_ID]
        if not CASE_PATTERN.fullmatch(stable_id):
            raise ValueError(f"invalid stable ID: {stable_id}")
        payload = definition[FIELD_PAYLOAD]
        if not payload[FIELD_TITLE].startswith(f"[{stable_id}]"):
            raise ValueError(f"title does not preserve stable ID: {stable_id}")
        for index, step in enumerate(payload[FIELD_STEPS], 1):
            role, separator, action = step[FIELD_ACTION].partition(": ")
            if not separator or not role or not action:
                raise ValueError(f"{stable_id} step {index} is not role-prefixed")
            if not step[FIELD_EXPECTED]:
                raise ValueError(f"{stable_id} step {index} has no oracle")


def _requested_view(document: dict[str, Any]) -> dict[str, Any]:
    return {
        FIELD_TITLE: document.get(FIELD_TITLE),
        FIELD_DESCRIPTION: document.get(FIELD_DESCRIPTION),
        FIELD_PRECONDITIONS: document.get(FIELD_PRECONDITIONS),
        FIELD_PRIORITY: document.get(FIELD_PRIORITY),
        FIELD_ESTIMATED_MINUTES: document.get(FIELD_ESTIMATED_MINUTES),
        FIELD_STEPS: [
            {
                FIELD_ACTION: step.get(FIELD_ACTION),
                FIELD_TEST_DATA: step.get(FIELD_TEST_DATA, ""),
                FIELD_EXPECTED: step.get(FIELD_EXPECTED),
            }
            for step in document.get(FIELD_STEPS, [])
        ],
    }


def verify_definition(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    actual_view = _requested_view(actual)
    for field in (
        FIELD_TITLE,
        FIELD_DESCRIPTION,
        FIELD_PRECONDITIONS,
        FIELD_PRIORITY,
        FIELD_ESTIMATED_MINUTES,
        FIELD_STEPS,
    ):
        if expected[field] != actual_view[field]:
            mismatches.append(field)
    if actual.get(FIELD_STATUS) != "RELEASED":
        mismatches.append(FIELD_STATUS)
    return mismatches


def ensure_cycle(
    *,
    base_url: str,
    project_id: str,
    token: str,
    package: PackageConfig = CAP01_PACKAGE,
    requester: Requester = request_json,
) -> dict[str, Any]:
    cycle_contract = package.cycle
    root = f"{base_url}/api/v1/projects/{project_id}/cycles"
    query = urlencode(
        {
            FIELD_BUILD: cycle_contract[FIELD_BUILD],
            FIELD_ENVIRONMENT: cycle_contract[FIELD_ENVIRONMENT],
            "page_size": 100,
        }
    )
    listed = requester(f"{root}?{query}", token)
    matches = [
        cycle
        for cycle in listed.get("results", [])
        if cycle.get(FIELD_NAME) == cycle_contract[FIELD_NAME]
        and cycle.get(FIELD_BUILD) == cycle_contract[FIELD_BUILD]
        and cycle.get(FIELD_ENVIRONMENT) == cycle_contract[FIELD_ENVIRONMENT]
    ]
    if len(matches) > 1:
        raise ValueError(f"multiple {package.capability} publication cycles exist")
    if matches:
        return matches[0]
    return requester(
        root,
        token,
        method=HTTP_POST,
        key=stable_key(
            "cycle-create", payload_sha256(cycle_contract), package.key_namespace
        ),
        payload=cycle_contract,
    )


def _find_definition(
    root: str, token: str, definition: dict[str, Any], requester: Requester
) -> dict[str, Any] | None:
    listed = requester(
        f"{root}?{urlencode({'q': definition['stable_id'], 'page_size': 100})}",
        token,
    )
    title = definition[FIELD_PAYLOAD][FIELD_TITLE]
    matches = [
        item
        for item in listed.get("results", [])
        if (item.get("latest_version") or {}).get(FIELD_TITLE) == title
    ]
    if len(matches) > 1:
        raise ValueError(f"duplicate remote definition: {definition['stable_id']}")
    return matches[0] if matches else None


def _version_url(root: str, testcase_id: str, version_id: str) -> str:
    return f"{root}/{testcase_id}/versions/{version_id}"


def publish_definition(
    *,
    root: str,
    cycle_id: str,
    token: str,
    definition: dict[str, Any],
    command_revision: str,
    key_namespace: str = "cap01",
    requester: Requester = request_json,
) -> dict[str, Any]:
    expected = definition[FIELD_PAYLOAD]
    item = _find_definition(root, token, definition, requester)
    changed = False
    if item is None:
        document = requester(
            f"{root}:guided",
            token,
            method=HTTP_POST,
            key=stable_key(
                "guided-create",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
                key_namespace,
            ),
            payload={
                "cycle_id": cycle_id,
                FIELD_NAME: expected[FIELD_TITLE],
                FIELD_DESCRIPTION: expected[FIELD_DESCRIPTION],
                FIELD_PRIORITY: expected[FIELD_PRIORITY],
            },
        )
        changed = True
    else:
        latest = item.get("latest_version") or {}
        testcase_id = str(item.get(FIELD_ID, ""))
        version_id = str(latest.get(FIELD_ID, ""))
        if not testcase_id or not version_id:
            raise ValueError(
                f"remote definition has no current version: {definition['stable_id']}"
            )
        document = requester(_version_url(root, testcase_id, version_id), token)

    testcase = document.get("testcase") or {}
    testcase_id = str(testcase.get(FIELD_ID, ""))
    version_id = str(document.get(FIELD_ID, ""))
    if not testcase_id or not version_id:
        raise ValueError(
            f"definition response has no identity: {definition['stable_id']}"
        )

    mismatches = verify_definition(expected, document)
    if document.get(FIELD_STATUS) == "RELEASED" and mismatches:
        document = requester(
            f"{root}/{testcase_id}:open-for-edit",
            token,
            method=HTTP_POST,
            key=stable_key(
                "open-edit",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
                key_namespace,
            ),
            if_match=f'"{testcase.get("revision")}"',
            payload={"source_version_id": version_id},
        )
        version_id = str(document.get(FIELD_ID, ""))
        changed = True

    if document.get(FIELD_STATUS) != "RELEASED":
        if _requested_view(document) != expected:
            document = requester(
                _version_url(root, testcase_id, version_id),
                token,
                method="PATCH",
                if_match=f'"{document.get("revision")}"',
                payload=expected,
            )
            changed = True
        document = requester(
            f"{_version_url(root, testcase_id, version_id)}:release",
            token,
            method=HTTP_POST,
            key=stable_key(
                "release",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
                key_namespace,
            ),
            if_match=f'"{document.get("revision")}"',
            payload={},
        )
        changed = True

    readback = requester(_version_url(root, testcase_id, version_id), token)
    mismatches = verify_definition(expected, readback)
    if mismatches:
        raise ValueError(
            f"readback mismatch for {definition['stable_id']}: {', '.join(mismatches)}"
        )
    return {
        FIELD_STABLE_ID: definition[FIELD_STABLE_ID],
        "testcase_id": testcase_id,
        "testcase_key": (readback.get("testcase") or {}).get("key"),
        "version_id": version_id,
        "version_number": readback.get("number"),
        "source_sha256": definition["source_sha256"],
        "payload_sha256": definition["payload_sha256"],
        FIELD_STATUS: readback.get(FIELD_STATUS),
        "changed": changed,
        FIELD_VERIFIED: True,
    }


def publish_manifest(
    *,
    base_url: str,
    project_id: str,
    token: str,
    manifest: dict[str, Any],
    command_revision: str,
    requester: Requester = request_json,
) -> dict[str, Any]:
    package = PACKAGES[manifest[FIELD_CAPABILITY]]
    cycle = ensure_cycle(
        base_url=base_url,
        project_id=project_id,
        token=token,
        package=package,
        requester=requester,
    )
    cycle_id = str(cycle.get(FIELD_ID, ""))
    if not cycle_id:
        raise ValueError(f"{package.capability} cycle response has no id")
    root = f"{base_url}/api/v1/projects/{project_id}/testcases"
    definitions = [
        publish_definition(
            root=root,
            cycle_id=cycle_id,
            token=token,
            definition=definition,
            command_revision=command_revision,
            key_namespace=package.key_namespace,
            requester=requester,
        )
        for definition in manifest[FIELD_DEFINITIONS]
    ]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": project_id,
        FIELD_CAPABILITY: manifest[FIELD_CAPABILITY],
        "workorder": manifest["workorder"],
        FIELD_MANIFEST_SHA256: manifest[FIELD_MANIFEST_SHA256],
        "command_revision": command_revision,
        "cycle": {
            FIELD_ID: cycle_id,
            FIELD_NAME: cycle.get(FIELD_NAME),
            FIELD_STATUS: cycle.get(FIELD_STATUS),
            FIELD_BUILD: cycle.get(FIELD_BUILD),
            FIELD_ENVIRONMENT: cycle.get(FIELD_ENVIRONMENT),
        },
        FIELD_DEFINITIONS: definitions,
        "execution_results_created": 0,
        FIELD_VERIFIED: all(definition[FIELD_VERIFIED] for definition in definitions),
    }


def _failure_receipt(
    *,
    project_id: str,
    base_url: str,
    token: str,
    manifest: dict[str, Any],
    command_revision: str,
    error: Exception,
) -> dict[str, Any]:
    failure: dict[str, Any] = {
        "stage": "definition-publication",
        "error_type": type(error).__name__,
        "detail": str(error) or type(error).__name__,
    }
    if isinstance(error, ApiError):
        failure["problem"] = {
            FIELD_STATUS: error.status,
            "code": error.code,
            "type": error.problem_type,
            FIELD_TITLE: error.title,
            "request_id": error.request_id,
            "errors": error.errors,
        }
    return redact(
        {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "project_id": project_id,
            "base_url": base_url,
            FIELD_MANIFEST_SHA256: manifest[FIELD_MANIFEST_SHA256],
            "command_revision": command_revision,
            FIELD_VERIFIED: False,
            "failure": failure,
        },
        (token,),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--package", choices=sorted(PACKAGES), default="CAP-01")
    parser.add_argument("--manual-dir", type=Path)
    parser.add_argument("--outbox", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--command-revision")
    args = parser.parse_args()
    package = PACKAGES[args.package]
    manual_dir = args.manual_dir or package.manual_dir
    outbox = args.outbox or package.outbox
    receipt_path = args.receipt or package.receipt
    command_revision = args.command_revision or package.command_revision

    try:
        manifest = build_manifest(manual_dir, package)
    except (OSError, ValueError) as error:
        print(f"{package.capability} definition validation failed safely: {error}")
        return 1
    write_json_atomic(outbox, manifest)
    if not args.apply:
        print(
            f"{package.capability} definition manifest validated; "
            "remote publication was not requested."
        )
        return 0

    base_url = os.getenv("SOFTWARETEST_BASE_URL", "https://softwaretest.it").rstrip("/")
    project_id = os.getenv("SOFTWARETEST_PROJECT_ID", "")
    token = os.getenv("SOFTWARETEST_TOKEN", "")
    if not project_id or not token:
        print("BLOCKED: SOFTWARETEST_PROJECT_ID and SOFTWARETEST_TOKEN are required")
        return 2
    try:
        receipt = publish_manifest(
            base_url=base_url,
            project_id=project_id,
            token=token,
            manifest=manifest,
            command_revision=command_revision,
        )
        write_json_atomic(receipt_path, redact(receipt, (token,)))
        if not receipt[FIELD_VERIFIED]:
            print(
                f"{package.capability} definition publication failed "
                "readback verification."
            )
            return 1
        print(
            f"{package.capability} definitions published and verified without "
            "executing tests."
        )
        return 0
    except (ApiError, OSError, ValueError) as error:
        write_json_atomic(
            receipt_path,
            _failure_receipt(
                project_id=project_id,
                base_url=base_url,
                token=token,
                manifest=manifest,
                command_revision=command_revision,
                error=error,
            ),
        )
        print(
            f"{package.capability} definition publication failed safely: "
            f"{type(error).__name__}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
