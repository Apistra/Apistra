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
REF_KEY = "$ref"


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _component_schema(document: dict[str, object], name: str) -> dict[str, object]:
    components = _mapping(document.get("components"))
    schemas = _mapping(components.get("schemas"))
    return _mapping(schemas.get(name))


def _property_schema(schema: dict[str, object], name: str) -> dict[str, object]:
    return _mapping(_mapping(schema.get("properties")).get(name))


def _validate_steering_openapi(
    document: dict[str, object], expected: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    batch = expected["steering_batch_contract"]
    if not isinstance(batch, dict):
        return ["Steering batch contract is not an object"]
    import_items = _property_schema(
        _component_schema(document, "SteeringImportRequest"), "items"
    )
    item = _component_schema(document, "SteeringItemImportRequest")
    evidence = _property_schema(item, "evidence_status")
    evidence_name = str(evidence.get(REF_KEY, "")).rsplit("/", 1)[-1]
    evidence_values = _component_schema(document, evidence_name).get("enum")
    receipt = _component_schema(document, "SteeringImportReceipt")
    hash_contract = _property_schema(receipt, "payload_hash_contract")
    hash_contract_schema = {}
    all_of = hash_contract.get("allOf")
    if isinstance(all_of, list) and all_of and isinstance(all_of[0], dict):
        hash_contract_schema = all_of[0]
    hash_contract_name = str(hash_contract_schema.get(REF_KEY, "")).rsplit("/", 1)[-1]
    hash_contract_values = _component_schema(document, hash_contract_name).get("enum")
    limits = (
        (import_items.get("minItems"), batch["minimum_items"]),
        (import_items.get("maxItems"), batch["maximum_items"]),
        (
            _property_schema(item, "criteria").get("maxItems"),
            batch["maximum_criteria_per_item"],
        ),
        (
            _property_schema(item, "decisions").get("maxItems"),
            batch["maximum_decisions_per_item"],
        ),
    )
    if any(actual != wanted for actual, wanted in limits):
        errors.append("Steering OpenAPI list limits changed")
    if evidence_name != "SteeringEvidenceStatusEnum":
        errors.append("Steering evidence schema reference changed")
    if evidence_values != expected["steering_evidence_statuses"]:
        errors.append("Steering evidence OpenAPI enum changed")
    expected_hash = expected.get("steering_payload_hash_contract", {})
    if (
        not isinstance(expected_hash, dict)
        or hash_contract_name != "PayloadHashContractEnum"
        or hash_contract_values
        != [expected_hash.get("current_contract"), expected_hash.get("legacy_contract")]
    ):
        errors.append("Steering payload hash OpenAPI contract changed")
    return errors


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
    expected_guide = contract.get("integration_guide", {})
    if isinstance(expected_guide, dict):
        errors.extend(_validate_steering_openapi(document, expected_guide))
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


def _validate_steering_batch(
    steering: dict[str, object], expected: dict[str, object]
) -> list[str]:
    batch = steering.get("batch_contract", {})
    wanted = expected["steering_batch_contract"]
    if not isinstance(batch, dict) or not isinstance(wanted, dict):
        return ["Steering batch guide is absent"]
    if any(batch.get(field) != value for field, value in wanted.items()):
        return ["Steering batch contract changed"]
    return []


def _validate_steering_statuses(
    steering: dict[str, object], expected: dict[str, object]
) -> list[str]:
    statuses = steering.get("status_contract", {})
    if not isinstance(statuses, dict):
        return ["Steering status guide is absent"]
    if statuses.get("evidence_status") != expected["steering_evidence_statuses"]:
        return ["Steering evidence status contract changed"]
    return []


def _validate_steering_payload_hash(
    steering: dict[str, object], expected: dict[str, object]
) -> list[str]:
    observed = steering.get("payload_hash_contract", {})
    wanted = expected.get("steering_payload_hash_contract", {})
    if not isinstance(observed, dict) or not isinstance(wanted, dict):
        return ["Steering payload hash guide is absent"]
    compatibility = _mapping(_mapping(steering.get("idempotency")).get("compatibility"))
    checks = (
        observed.get("current_contract") == wanted.get("current_contract"),
        observed.get("operation_version") == wanted.get("operation_version"),
        observed.get("algorithm") == wanted.get("algorithm"),
        observed.get("canonicalization_uri") == wanted.get("canonicalization_uri"),
        wanted.get("legacy_contract") in str(compatibility.get("legacy", "")),
        "new idempotency-key" in str(compatibility.get("key_rotation", "")).lower(),
    )
    return [] if all(checks) else ["Steering payload hash contract changed"]


def _validate_steering_data(
    document: dict[str, object], expected: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    steering = document.get("steering_data", {})
    if not isinstance(steering, dict):
        return ["Steering integration guide is absent"]
    operations = steering.get("operations", {})
    operation_names = ("import", "list", "detail", "overview", "export")
    observed_operations = (
        [operations.get(name) for name in operation_names]
        if isinstance(operations, dict)
        else []
    )
    if observed_operations != expected["steering_operations"]:
        errors.append("Steering operation contract changed")
    checks = (
        (
            steering.get("required_scopes") == expected["steering_required_scopes"],
            "Steering required scopes changed",
        ),
        (
            steering.get("required_headers") == expected["steering_required_headers"],
            "Steering required headers changed",
        ),
        (
            steering.get("uses_if_match") is expected["steering_uses_if_match"],
            "Steering revision contract changed",
        ),
    )
    errors.extend(message for valid, message in checks if not valid)
    errors.extend(_validate_steering_batch(steering, expected))
    errors.extend(_validate_steering_statuses(steering, expected))
    errors.extend(_validate_steering_payload_hash(steering, expected))
    recovery = steering.get("failure_recovery", {})
    if not isinstance(recovery, dict) or not set(
        expected["steering_failure_codes"]
    ).issubset(recovery):
        errors.append("required Steering failure recovery codes are absent")
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
        *_validate_steering_data(document, expected),
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
