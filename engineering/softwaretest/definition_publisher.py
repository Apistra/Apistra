"""Publish reviewed CAP-01 manual definitions with verified readback.

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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from publisher import ApiError, payload_sha256, redact, request_json, write_json_atomic

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANUAL_DIR = ROOT / "docs/testing/manual/PRC-01"
DEFAULT_OUTBOX = ROOT / "artifacts/softwaretest-cap01-definition-outbox.json"
DEFAULT_RECEIPT = ROOT / "artifacts/softwaretest-cap01-definition-receipt.json"
CASE_PATTERN = re.compile(r"MT-PRC-01-\d{3}")
STEP_PATTERN = re.compile(r"^(\d+)\. \*\*(Action|Observation) \(([^)]+)\):\*\* (.+)$")
CYCLE = {
    "name": "Apistra CAP-01 Acceptance",
    "objective": (
        "Publish and later execute the approved CAP-01 administration and "
        "project-isolation acceptance package."
    ),
    "build": "CAP-01",
    "environment": "isolated-local-staging",
}

Requester = Callable[..., dict[str, Any]]


def stable_key(command: str, value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:24]
    return f"apistra-cap01-{command}-{digest}"


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


def _parse_steps(text: str) -> list[dict[str, str]]:
    procedure = _section(text, "Procedure", "Cleanup")
    steps: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    active_field = ""
    for raw_line in procedure.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = STEP_PATTERN.match(line)
        if match:
            if current:
                steps.append(current)
            number, kind, role, action = match.groups()
            current = {
                "number": number,
                "action": f"{role}: {action}",
                "test_data": "",
                "expected": "",
                "kind": kind,
            }
            active_field = "action"
            continue
        if current is None:
            raise ValueError("content found before the first procedure step")
        if line.startswith("**Test data:**"):
            current["test_data"] = line.removeprefix("**Test data:**").strip()
            active_field = "test_data"
        elif line.startswith("**Expected result:**"):
            current["expected"] = line.removeprefix("**Expected result:**").strip()
            active_field = "expected"
        elif active_field:
            current[active_field] = f"{current[active_field]} {line}".strip()
    if current:
        steps.append(current)

    for index, step in enumerate(steps, 1):
        if int(step.pop("number")) != index:
            raise ValueError("manual steps must be consecutively numbered")
        step.pop("kind")
        if not step["action"] or not step["expected"]:
            raise ValueError(f"step {index} has no action or expected result")
    if not steps:
        raise ValueError("manual case has no procedure steps")
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
            "stable_id": stable_id,
            "title": title,
            "objective": objective,
            "preconditions": preconditions,
            "traceability": traceability,
            "steps": steps,
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
        "title": f"[{stable_id}] {title}",
        "description": "\n".join(description_lines),
        "preconditions": preconditions,
        "priority": "HIGH",
        "estimated_minutes": 20,
        "steps": steps,
    }
    return {
        "stable_id": stable_id,
        "source_path": path.relative_to(ROOT).as_posix(),
        "source_sha256": source_sha256,
        "payload_sha256": payload_sha256(payload),
        "payload": payload,
        "traceability": traceability,
    }


def build_manifest(manual_dir: Path = DEFAULT_MANUAL_DIR) -> dict[str, Any]:
    definitions = [parse_case(path) for path in sorted(manual_dir.glob("MT-*.md"))]
    manifest = {
        "schema_version": "1.0",
        "capability": "CAP-01",
        "process": "PRC-01",
        "workorder": "WO-CAP-01-04",
        "cycle": CYCLE,
        "definitions": definitions,
    }
    validate_manifest(manifest)
    manifest["manifest_sha256"] = payload_sha256(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    definitions = manifest.get("definitions", [])
    if len(definitions) != 6:
        raise ValueError("CAP-01 package must contain exactly six manual definitions")
    stable_ids = [definition["stable_id"] for definition in definitions]
    if len(set(stable_ids)) != len(stable_ids):
        raise ValueError("manual definition IDs must be unique")
    for definition in definitions:
        stable_id = definition["stable_id"]
        if not CASE_PATTERN.fullmatch(stable_id):
            raise ValueError(f"invalid stable ID: {stable_id}")
        payload = definition["payload"]
        if not payload["title"].startswith(f"[{stable_id}]"):
            raise ValueError(f"title does not preserve stable ID: {stable_id}")
        for index, step in enumerate(payload["steps"], 1):
            role, separator, action = step["action"].partition(": ")
            if not separator or not role or not action:
                raise ValueError(f"{stable_id} step {index} is not role-prefixed")
            if not step["expected"]:
                raise ValueError(f"{stable_id} step {index} has no oracle")


def _requested_view(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": document.get("title"),
        "description": document.get("description"),
        "preconditions": document.get("preconditions"),
        "priority": document.get("priority"),
        "estimated_minutes": document.get("estimated_minutes"),
        "steps": [
            {
                "action": step.get("action"),
                "test_data": step.get("test_data", ""),
                "expected": step.get("expected"),
            }
            for step in document.get("steps", [])
        ],
    }


def verify_definition(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    actual_view = _requested_view(actual)
    for field in (
        "title",
        "description",
        "preconditions",
        "priority",
        "estimated_minutes",
        "steps",
    ):
        if expected[field] != actual_view[field]:
            mismatches.append(field)
    if actual.get("status") != "RELEASED":
        mismatches.append("status")
    return mismatches


def ensure_cycle(
    *, base_url: str, project_id: str, token: str, requester: Requester
) -> dict[str, Any]:
    root = f"{base_url}/api/v1/projects/{project_id}/cycles"
    query = urlencode(
        {
            "build": CYCLE["build"],
            "environment": CYCLE["environment"],
            "page_size": 100,
        }
    )
    listed = requester(f"{root}?{query}", token)
    matches = [
        cycle
        for cycle in listed.get("results", [])
        if cycle.get("name") == CYCLE["name"]
        and cycle.get("build") == CYCLE["build"]
        and cycle.get("environment") == CYCLE["environment"]
    ]
    if len(matches) > 1:
        raise ValueError("multiple CAP-01 publication cycles exist")
    if matches:
        return matches[0]
    return requester(
        root,
        token,
        method="POST",
        key=stable_key("cycle-create", payload_sha256(CYCLE)),
        payload=CYCLE,
    )


def _find_definition(
    root: str, token: str, definition: dict[str, Any], requester: Requester
) -> dict[str, Any] | None:
    listed = requester(
        f"{root}?{urlencode({'q': definition['stable_id'], 'page_size': 100})}",
        token,
    )
    title = definition["payload"]["title"]
    matches = [
        item
        for item in listed.get("results", [])
        if (item.get("latest_version") or {}).get("title") == title
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
    requester: Requester,
) -> dict[str, Any]:
    expected = definition["payload"]
    item = _find_definition(root, token, definition, requester)
    changed = False
    if item is None:
        document = requester(
            f"{root}:guided",
            token,
            method="POST",
            key=stable_key(
                "guided-create",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
            ),
            payload={
                "cycle_id": cycle_id,
                "name": expected["title"],
                "description": expected["description"],
                "priority": expected["priority"],
            },
        )
        changed = True
    else:
        latest = item.get("latest_version") or {}
        testcase_id = str(item.get("id", ""))
        version_id = str(latest.get("id", ""))
        if not testcase_id or not version_id:
            raise ValueError(
                f"remote definition has no current version: {definition['stable_id']}"
            )
        document = requester(_version_url(root, testcase_id, version_id), token)

    testcase = document.get("testcase") or {}
    testcase_id = str(testcase.get("id", ""))
    version_id = str(document.get("id", ""))
    if not testcase_id or not version_id:
        raise ValueError(
            f"definition response has no identity: {definition['stable_id']}"
        )

    mismatches = verify_definition(expected, document)
    if document.get("status") == "RELEASED" and mismatches:
        document = requester(
            f"{root}/{testcase_id}:open-for-edit",
            token,
            method="POST",
            key=stable_key(
                "open-edit",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
            ),
            if_match=f'"{testcase.get("revision")}"',
            payload={"source_version_id": version_id},
        )
        version_id = str(document.get("id", ""))
        changed = True

    if document.get("status") != "RELEASED":
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
            method="POST",
            key=stable_key(
                "release",
                f"{definition['stable_id']}:{definition['source_sha256']}:{command_revision}",
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
        "stable_id": definition["stable_id"],
        "testcase_id": testcase_id,
        "testcase_key": (readback.get("testcase") or {}).get("key"),
        "version_id": version_id,
        "version_number": readback.get("number"),
        "source_sha256": definition["source_sha256"],
        "payload_sha256": definition["payload_sha256"],
        "status": readback.get("status"),
        "changed": changed,
        "verified": True,
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
    cycle = ensure_cycle(
        base_url=base_url,
        project_id=project_id,
        token=token,
        requester=requester,
    )
    cycle_id = str(cycle.get("id", ""))
    if not cycle_id:
        raise ValueError("CAP-01 cycle response has no id")
    root = f"{base_url}/api/v1/projects/{project_id}/testcases"
    definitions = [
        publish_definition(
            root=root,
            cycle_id=cycle_id,
            token=token,
            definition=definition,
            command_revision=command_revision,
            requester=requester,
        )
        for definition in manifest["definitions"]
    ]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": project_id,
        "capability": manifest["capability"],
        "workorder": manifest["workorder"],
        "manifest_sha256": manifest["manifest_sha256"],
        "command_revision": command_revision,
        "cycle": {
            "id": cycle_id,
            "name": cycle.get("name"),
            "status": cycle.get("status"),
            "build": cycle.get("build"),
            "environment": cycle.get("environment"),
        },
        "definitions": definitions,
        "execution_results_created": 0,
        "verified": all(definition["verified"] for definition in definitions),
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
            "status": error.status,
            "code": error.code,
            "type": error.problem_type,
            "title": error.title,
            "request_id": error.request_id,
            "errors": error.errors,
        }
    return redact(
        {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "project_id": project_id,
            "base_url": base_url,
            "manifest_sha256": manifest["manifest_sha256"],
            "command_revision": command_revision,
            "verified": False,
            "failure": failure,
        },
        (token,),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--manual-dir", type=Path, default=DEFAULT_MANUAL_DIR)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--command-revision", default="cap01-definitions-v1")
    args = parser.parse_args()

    try:
        manifest = build_manifest(args.manual_dir)
    except (OSError, ValueError) as error:
        print(f"CAP-01 definition validation failed safely: {error}")
        return 1
    write_json_atomic(args.outbox, manifest)
    if not args.apply:
        print(
            "CAP-01 definition manifest validated; remote publication was not requested."
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
            command_revision=args.command_revision,
        )
        write_json_atomic(args.receipt, redact(receipt, (token,)))
        if not receipt["verified"]:
            print("CAP-01 definition publication failed readback verification.")
            return 1
        print("CAP-01 definitions published and verified without executing tests.")
        return 0
    except (ApiError, OSError, ValueError) as error:
        write_json_atomic(
            args.receipt,
            _failure_receipt(
                project_id=project_id,
                base_url=base_url,
                token=token,
                manifest=manifest,
                command_revision=args.command_revision,
                error=error,
            ),
        )
        print(f"CAP-01 definition publication failed safely: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
