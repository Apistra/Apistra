"""Verify the public contract and optionally the protected project binding."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLIC_GUIDE_TIMEOUT_SECONDS = 15


def validate_openapi(
    document: dict[str, object], contract: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    info = document.get("info", {})
    if document.get("openapi") != contract["openapi_version"]:
        errors.append("OpenAPI version changed")
    if not isinstance(info, dict) or info.get("title") != contract["api_title"]:
        errors.append("API title changed")
    if not isinstance(info, dict) or info.get("version") != contract["api_version"]:
        errors.append("API version changed")
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        return [*errors, "paths is not an object"]
    for name, operation in contract["operations"].items():
        method, path = operation
        if path not in paths or method.lower() not in paths[path]:
            errors.append(f"required operation {name} is absent")
    schemes = document.get("components", {}).get("securitySchemes", {})
    if contract["authentication"]["scheme"] not in schemes:
        errors.append("ProjectBearer security scheme is absent")
    return errors


def _validate_command_protocol(
    document: dict[str, object], expected: dict[str, object]
) -> list[str]:
    protocol = document.get("command_protocol", {})
    if not isinstance(protocol, dict):
        return ["integration guide command protocol is absent"]
    checks = (
        (
            protocol.get("read_before_write") is True,
            "read-before-write is no longer required",
        ),
        (
            protocol.get("revision_header") == expected["revision_header"],
            "revision header changed",
        ),
        (
            protocol.get("idempotency_header") == expected["idempotency_header"],
            "idempotency header changed",
        ),
    )
    return [message for valid, message in checks if not valid]


def _operation_ids(section: dict[str, object]) -> list[object]:
    return [
        step.get("operation_id")
        for step in section.get("steps", [])
        if isinstance(step, dict)
    ]


def _validate_cycle_execution(
    document: dict[str, object], expected: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    execution = document.get("cycle_execution", {})
    if not isinstance(execution, dict):
        return ["cycle execution guide is absent"]
    if _operation_ids(execution) != expected["cycle_operations"]:
        errors.append("cycle execution operation order changed")
    preconditions = execution.get("start_preconditions", {})
    if not isinstance(preconditions, dict):
        errors.append("cycle start preconditions are absent")
    elif (
        preconditions.get("cycle_status") != "DRAFT"
        or preconditions.get("minimum_run_count") != 1
        or preconditions.get("current_revision_required") is not True
        or execution.get("planned_window_required") is not False
    ):
        errors.append("cycle start preconditions changed")
    recovery = execution.get("failure_recovery", {})
    if not isinstance(recovery, dict) or not set(
        expected["cycle_failure_codes"]
    ).issubset(recovery):
        errors.append("required failure recovery codes are absent")
    return errors


def _validate_reporting_prerequisites(
    reporting: dict[str, object], expected: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    prerequisites = reporting.get("prerequisites", {})
    if not isinstance(prerequisites, dict):
        return ["CI reporting prerequisites are absent"]
    automation_resource = str(prerequisites.get("automation_resource", ""))
    automation_required = (
        "no pre-provisioned automation resource" not in automation_resource.lower()
    )
    if automation_required != expected["automation_resource_required"]:
        errors.append("CI reporting automation-resource prerequisite changed")
    if not prerequisites.get("cycle") or not prerequisites.get("project"):
        errors.append("CI reporting project/cycle prerequisites are absent")
    return errors


def _validate_ci_reporting(
    document: dict[str, object], expected: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    reporting = document.get("ci_reporting", {})
    if not isinstance(reporting, dict):
        return ["CI reporting guide is absent"]
    if _operation_ids(reporting) != expected["reporting_operations"]:
        errors.append("CI reporting operation order changed")
    if reporting.get("required_scopes") != expected["reporting_required_scopes"]:
        errors.append("CI reporting required scopes changed")
    if reporting.get("required_headers") != expected["reporting_required_headers"]:
        errors.append("CI reporting required headers changed")
    if reporting.get("uses_if_match") is not expected["reporting_uses_if_match"]:
        errors.append("CI reporting revision contract changed")
    errors.extend(_validate_reporting_prerequisites(reporting, expected))
    reporting_recovery = reporting.get("failure_recovery", {})
    if not isinstance(reporting_recovery, dict) or not set(
        expected["reporting_failure_codes"]
    ).issubset(reporting_recovery):
        errors.append("required CI reporting failure recovery codes are absent")
    return errors


def validate_integration_guide(
    document: dict[str, object], contract: dict[str, object]
) -> list[str]:
    expected = contract["integration_guide"]
    if not isinstance(expected, dict):
        return ["integration guide contract is not an object"]
    errors = []
    if document.get("contract") != expected["contract"]:
        errors.append("integration guide contract changed")
    if document.get("version") != expected["version"]:
        errors.append("integration guide version changed")
    return [
        *errors,
        *_validate_command_protocol(document, expected),
        *_validate_cycle_execution(document, expected),
        *_validate_ci_reporting(document, expected),
    ]


def get_json(url: str, token: str | None = None) -> dict[str, object]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers),
        timeout=PUBLIC_GUIDE_TIMEOUT_SECONDS,
    ) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=HERE / "contract.json")
    parser.add_argument("--openapi-file", type=Path)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--require-reporting", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    base_url = (os.getenv("SOFTWARETEST_BASE_URL") or contract["base_url"]).rstrip("/")
    try:
        document = (
            json.loads(args.openapi_file.read_text(encoding="utf-8"))
            if args.openapi_file
            else get_json(base_url + contract["openapi_path"])
        )
        guide = get_json(base_url + contract["integration_guide"]["path"])
        errors = [
            *validate_openapi(document, contract),
            *validate_integration_guide(guide, contract),
        ]
        if errors:
            print("; ".join(errors))
            return 1
        project_id = os.getenv("SOFTWARETEST_PROJECT_ID")
        token = os.getenv("SOFTWARETEST_TOKEN")
        if args.require_auth or args.require_reporting:
            if not project_id or not token:
                print(
                    "BLOCKED: SOFTWARETEST_PROJECT_ID and SOFTWARETEST_TOKEN are required"
                )
                return 2
            project = get_json(f"{base_url}/api/v1/projects/{project_id}", token)
            if project.get("id") != project_id:
                print("Authenticated project round-trip returned a different project")
                return 1
        if args.require_reporting:
            cycles = get_json(f"{base_url}/api/v1/projects/{project_id}/cycles", token)
            reports = get_json(
                f"{base_url}/api/v1/projects/{project_id}/ci-reports", token
            )
            steering = get_json(
                f"{base_url}/api/v1/projects/{project_id}/steering/export", token
            )
            if not isinstance(cycles.get("results"), list):
                print("Authenticated cycle listing has an unexpected shape")
                return 1
            if not isinstance(reports.get("results"), list):
                print("Authenticated CI-report listing has an unexpected shape")
                return 1
            if not isinstance(steering.get("items"), list):
                print("Authenticated Steering export has an unexpected shape")
                return 1
        print("Softwaretest.it contract preflight passed.")
        return 0
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Softwaretest.it preflight failed safely: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
