"""Lossless CAP-00 CI-report publisher with verified readback and receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ALLOWED_STATUSES = {"PASSED", "FAILED", "SKIPPED", "ERROR", "CANCELLED"}
PROBLEM_FIELD_LIMIT = 200
PROBLEM_DETAIL_LIMIT = 500
DEFAULT_API_TIMEOUT_SECONDS = 30
UTC_SUFFIX = "Z"
UTC_OFFSET = "+00:00"
FIELD_RESULTS = "results"
FIELD_STATUS = "status"
FIELD_STARTED_AT = "started_at"
FIELD_FINISHED_AT = "finished_at"
FIELD_JOB_ID = "job_id"
FIELD_NAME = "name"
FIELD_ENTRIES = "entries"
FIELD_REPORT_ID = "report_id"
FIELD_ID = "id"
LOCAL_PIPELINE_ID = "local"
DEFAULT_JOB_ID = "cap00-candidate"
CAP00_STAGE_ID = "cap00"
HTTP_GET = "GET"
HTTP_POST = "POST"
RESOURCE_CYCLE = "cycle"
COMMAND_CREATE = "create"
COMMAND_FINALIZE = "finalize"
COMMAND_START = "start"
STATUS_DRAFT = "DRAFT"
DRAFT_CYCLE_LABEL = "draft cycle"


class ApiError(RuntimeError):
    """Sanitised API failure containing no request headers or credentials."""

    def __init__(self, status: int, problem: dict[str, Any]) -> None:
        self.status = status
        self.code = str(problem.get("code", ""))[:100]
        self.problem_type = str(problem.get("type", ""))[:PROBLEM_FIELD_LIMIT]
        self.title = str(problem.get("title", ""))[:PROBLEM_FIELD_LIMIT]
        self.detail = str(problem.get("detail", ""))[:PROBLEM_DETAIL_LIMIT]
        self.request_id = str(problem.get("request_id", ""))[:PROBLEM_FIELD_LIMIT]
        raw_errors = problem.get("errors", {})
        self.errors = raw_errors if isinstance(raw_errors, dict) else {}
        summary = self.code or self.title or self.problem_type or "API request failed"
        if self.detail:
            summary = f"{summary}: {self.detail}"
        if self.request_id:
            summary = f"{summary} (request_id={self.request_id})"
        super().__init__(f"HTTP {status} {summary}")


def stable_key(prefix: str, value: str) -> str:
    return f"apistra-cap00-{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:24]}"


def command_key(
    pipeline_run_id: str,
    resource_type: str,
    resource_id: str,
    command: str,
    revision: int | str,
    attempt: int,
) -> str:
    value = (
        f"{pipeline_run_id}:{resource_type}:{resource_id}:{command}:"
        f"rev-{revision}:attempt-{attempt}"
    )
    return stable_key(f"{resource_type}-{command}", value)


def payload_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def redact(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {key: redact(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, str):
        cleaned = value
        for secret in secrets:
            if secret:
                cleaned = cleaned.replace(secret, "[REDACTED]")
        return cleaned
    return value


def canonical_datetime(value: str) -> str:
    """Return an RFC 3339 UTC timestamp at the API's millisecond precision."""
    parsed = datetime.fromisoformat(value.replace(UTC_SUFFIX, UTC_OFFSET))
    if parsed.tzinfo is None:
        raise ValueError("report timestamps must include a timezone")
    return (
        parsed.astimezone(UTC)
        .isoformat(timespec="milliseconds")
        .replace(UTC_OFFSET, UTC_SUFFIX)
    )


def aggregate_stage_status(statuses: set[str]) -> str:
    """Derive the required stage result without hiding a non-passing test."""
    if not statuses:
        raise ValueError("at least one result is required")
    for status in ("ERROR", "FAILED", "CANCELLED"):
        if status in statuses:
            return status
    if statuses == {"SKIPPED"}:
        return "SKIPPED"
    return "PASSED"


def build_payloads(
    bundle: dict[str, Any], cycle_id: str
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    now = canonical_datetime(datetime.now(UTC).isoformat())
    candidate = bundle["candidate"]
    results = bundle[FIELD_RESULTS]
    statuses = {result[FIELD_STATUS] for result in results}
    unsupported = statuses - ALLOWED_STATUSES
    if unsupported:
        raise ValueError(f"unsupported result statuses: {sorted(unsupported)}")
    started_at = canonical_datetime(bundle.get(FIELD_STARTED_AT, now))
    finished_at = canonical_datetime(bundle.get(FIELD_FINISHED_AT, now))
    report = {
        "cycle_id": cycle_id,
        "external_key": f"cap00-{candidate['commit']}",
        "pipeline_id": bundle.get("pipeline_id", LOCAL_PIPELINE_ID),
        FIELD_JOB_ID: bundle.get(FIELD_JOB_ID, DEFAULT_JOB_ID),
        "commit_sha": candidate["commit"],
        "artifact_digest": candidate["manifest_sha256"],
        FIELD_STARTED_AT: started_at,
        "contract_version": "1.0",
        "source_repository": "Apistra/Apistra",
        "capability_ids": ["CAP-00"],
        "workorder_ids": [f"WO-CAP-00-{index:02d}" for index in range(1, 8)],
        "required_stages": [
            {
                "stage_id": CAP00_STAGE_ID,
                FIELD_JOB_ID: DEFAULT_JOB_ID,
                "expected_tests": len(results),
                "required": True,
            }
        ],
    }
    test_entries = [
        {
            "kind": "test",
            "stage_id": CAP00_STAGE_ID,
            FIELD_JOB_ID: DEFAULT_JOB_ID,
            "suite": result.get("suite", CAP00_STAGE_ID),
            "test_id": result["test_id"],
            FIELD_NAME: result.get(FIELD_NAME, result["test_id"]),
            "attempt_no": result.get("attempt_no", 1),
            FIELD_STATUS: result[FIELD_STATUS],
            FIELD_STARTED_AT: canonical_datetime(result.get(FIELD_STARTED_AT, now)),
            FIELD_FINISHED_AT: canonical_datetime(result.get(FIELD_FINISHED_AT, now)),
            "duration_ms": int(result.get("duration_ms", 0)),
            "error_details": result.get("error_details", ""),
            "metrics": result.get("metrics", []),
            "findings": result.get("findings", []),
            "attachments": result.get("attachments", []),
        }
        for result in results
    ]
    stage_entry = {
        "kind": "stage",
        "stage_id": CAP00_STAGE_ID,
        FIELD_JOB_ID: DEFAULT_JOB_ID,
        "suite": "CAP-00",
        FIELD_NAME: "CAP-00 required CI stage",
        "attempt_no": 1,
        FIELD_STATUS: aggregate_stage_status(statuses),
        FIELD_STARTED_AT: started_at,
        FIELD_FINISHED_AT: finished_at,
        "duration_ms": 0,
        "error_details": "",
        "metrics": [],
        "findings": [],
        "attachments": [],
    }
    return report, [stage_entry, *test_entries], {FIELD_FINISHED_AT: finished_at}


def request_json(
    url: str,
    token: str,
    *,
    method: str = HTTP_GET,
    key: str = "",
    if_match: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if key:
        headers["Idempotency-Key"] = key
    if if_match:
        headers["If-Match"] = if_match
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(
            request, timeout=DEFAULT_API_TIMEOUT_SECONDS
        ) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            problem = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            problem = {}
        raise ApiError(error.code, problem) from None


def _compare_mapping(
    expected: dict[str, Any], actual: Any, path: str, mismatches: list[str]
) -> None:
    if not isinstance(actual, dict):
        mismatches.append(f"{path}: expected object")
        return
    for key, value in expected.items():
        if key not in actual:
            mismatches.append(f"{path}.{key}: missing")
            continue
        _compare_requested(value, actual[key], f"{path}.{key}", mismatches)


def _compare_sequence(
    expected: list[Any], actual: Any, path: str, mismatches: list[str]
) -> None:
    if not isinstance(actual, list):
        mismatches.append(f"{path}: expected array")
        return
    if len(expected) != len(actual):
        mismatches.append(
            f"{path}: expected {len(expected)} items, received {len(actual)}"
        )
        return
    for index, value in enumerate(expected):
        _compare_requested(value, actual[index], f"{path}[{index}]", mismatches)


def _equivalent_timestamp(expected: Any, actual: Any, path: str) -> bool:
    if not (
        isinstance(expected, str)
        and isinstance(actual, str)
        and path.endswith((FIELD_STARTED_AT, FIELD_FINISHED_AT))
    ):
        return False
    try:
        expected_time = datetime.fromisoformat(expected.replace(UTC_SUFFIX, UTC_OFFSET))
        actual_time = datetime.fromisoformat(actual.replace(UTC_SUFFIX, UTC_OFFSET))
    except ValueError:
        return False
    return expected_time == actual_time


def _compare_requested(
    expected: Any, actual: Any, path: str, mismatches: list[str]
) -> None:
    if isinstance(expected, dict):
        _compare_mapping(expected, actual, path, mismatches)
        return
    if isinstance(expected, list):
        _compare_sequence(expected, actual, path, mismatches)
        return
    if _equivalent_timestamp(expected, actual, path):
        return
    if expected != actual:
        mismatches.append(f"{path}: value differs")


def verify_readback(
    report: dict[str, Any], entries: list[dict[str, Any]], document: dict[str, Any]
) -> list[str]:
    """Compare every submitted field while allowing server-owned response fields."""
    mismatches: list[str] = []
    _compare_requested(report, document.get("manifest"), "manifest", mismatches)
    _compare_requested(entries, document.get(FIELD_ENTRIES), FIELD_ENTRIES, mismatches)
    if str(document.get(FIELD_STATUS, "")).upper() not in {"FINALIZED", "COMPLETE"}:
        mismatches.append("status: report is not finalised")
    if str(document.get("completeness", "")).upper() != "COMPLETE":
        mismatches.append("completeness: required stages or tests are missing")
    return mismatches


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_failure_receipt(
    path: Path,
    *,
    project_id: str,
    base_url: str,
    token: str,
    command_revision: str,
    stage: str,
    error: Exception,
    cycle: dict[str, Any] | None = None,
    request_sha256: dict[str, str] | None = None,
) -> None:
    """Retain redacted machine-readable evidence for a failed remote operation."""
    evidence: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": project_id,
        "base_url": base_url,
        RESOURCE_CYCLE: cycle or {},
        "command_revision": command_revision,
        "verified": False,
        "failure": {
            "stage": stage,
            "error_type": type(error).__name__,
            "detail": str(error) or type(error).__name__,
        },
    }
    if request_sha256:
        evidence["request_sha256"] = request_sha256
    if isinstance(error, ApiError):
        evidence["failure"]["problem"] = {
            FIELD_STATUS: error.status,
            "code": error.code,
            "type": error.problem_type,
            "title": error.title,
            "request_id": error.request_id,
            "errors": error.errors,
        }
    write_json_atomic(path, redact(evidence, (token,)))


def execute_roundtrip(
    *,
    base_url: str,
    project_id: str,
    token: str,
    report: dict[str, Any],
    entries: list[dict[str, Any]],
    final: dict[str, str],
    command_revision: str = "v1",
    requester=request_json,
) -> dict[str, Any]:
    root = f"{base_url}/api/v1/projects/{project_id}/ci-reports"
    external_key = report["external_key"]
    commands = (
        (COMMAND_CREATE, root, report),
        (FIELD_ENTRIES, "", {FIELD_ENTRIES: entries}),
        (COMMAND_FINALIZE, "", final),
    )
    receipts: dict[str, Any] = {}
    report_id = ""
    for command, configured_url, payload in commands:
        url = configured_url or f"{root}/{report_id}/{command}"
        response = requester(
            url,
            token,
            method=HTTP_POST,
            key=stable_key(command, f"{external_key}:{command_revision}"),
            payload=payload,
        )
        if command == COMMAND_CREATE:
            report_id = response.get(FIELD_REPORT_ID, "")
            if not report_id:
                raise ValueError("create response has no report_id")
        if response.get(FIELD_REPORT_ID) != report_id:
            raise ValueError(f"{command} receipt references another report")
        receipts[command] = response

    document = requester(f"{root}/{report_id}", token, method=HTTP_GET)
    if document.get(FIELD_REPORT_ID) != report_id:
        raise ValueError("readback references another report")
    mismatches = verify_readback(report, entries, document)

    receipt_documents: dict[str, Any] = {}
    receipt_root = f"{base_url}/api/v1/projects/{project_id}/reporting-receipts"
    for command, receipt in receipts.items():
        receipt_id = receipt.get("receipt_id")
        if receipt_id:
            receipt_documents[command] = requester(
                f"{receipt_root}/{receipt_id}", token, method=HTTP_GET
            )

    return {
        FIELD_REPORT_ID: report_id,
        "verified": not mismatches,
        "mismatches": mismatches,
        "request_sha256": {
            COMMAND_CREATE: payload_sha256(report),
            FIELD_ENTRIES: payload_sha256({FIELD_ENTRIES: entries}),
            COMMAND_FINALIZE: payload_sha256(final),
        },
        "server_receipts": receipts,
        "receipt_readbacks": receipt_documents,
        "report_readback": document,
    }


def _revision(document: dict[str, Any], resource: str) -> int:
    value = document.get("revision")
    if not isinstance(value, int):
        raise TypeError(f"{resource} has no revision")
    return value


def _find_cycle(page: dict[str, Any], cycle_id: str) -> dict[str, Any] | None:
    return next(
        (
            cycle
            for cycle in page.get(FIELD_RESULTS, [])
            if isinstance(cycle, dict) and cycle.get(FIELD_ID) == cycle_id
        ),
        None,
    )


def _refresh_cycle(url: str, token: str, cycle_id: str, requester) -> dict[str, Any]:
    selected = _find_cycle(requester(url, token, method=HTTP_GET), cycle_id)
    if selected is None:
        raise ValueError("cycle disappeared from project listing")
    return selected


def _problem_context(error: ApiError) -> str:
    parts = [error.code or "API_ERROR"]
    failed = error.errors.get("failed_precondition")
    current_etag = error.errors.get("current_etag")
    if failed:
        parts.append(f"failed_precondition={failed}")
    if current_etag:
        parts.append(f"current_etag={current_etag}")
    if error.request_id:
        parts.append(f"request_id={error.request_id}")
    return "; ".join(parts)


def _read_cycle_runs(
    *, base_url: str, project_id: str, cycle_id: str, token: str, requester
) -> list[dict[str, Any]]:
    query = urlencode({RESOURCE_CYCLE: cycle_id, "page_size": 100})
    page = requester(
        f"{base_url}/api/v1/projects/{project_id}/runs?{query}",
        token,
        method=HTTP_GET,
    )
    results = page.get(FIELD_RESULTS, [])
    if not isinstance(results, list):
        raise TypeError("run listing has an unexpected shape")
    return [
        run
        for run in results
        if isinstance(run, dict) and run.get("cycle_id") == cycle_id
    ]


def _start_cycle_run(
    *,
    base_url: str,
    project_id: str,
    cycle_id: str,
    token: str,
    pipeline_run_id: str,
    requester,
) -> dict[str, Any]:
    runs = _read_cycle_runs(
        base_url=base_url,
        project_id=project_id,
        cycle_id=cycle_id,
        token=token,
        requester=requester,
    )
    in_progress = [run for run in runs if run.get(FIELD_STATUS) == "IN_PROGRESS"]
    if in_progress:
        return in_progress[0]
    startable = [run for run in runs if run.get(FIELD_STATUS) == "NOT_STARTED"]
    if not startable:
        raise ValueError("active cycle has no NOT_STARTED or IN_PROGRESS run")
    selected = startable[0]
    run_id = str(selected.get(FIELD_ID, ""))
    if not run_id:
        raise ValueError("planned run has no id")
    revision = _revision(selected, "planned run")
    url = f"{base_url}/api/v1/projects/{project_id}/runs/{run_id}:start"
    try:
        started = requester(
            url,
            token,
            method=HTTP_POST,
            key=command_key(pipeline_run_id, "run", run_id, COMMAND_START, revision, 1),
            if_match=f'"{revision}"',
        )
    except ApiError as error:
        if error.code != "REVISION_CONFLICT":
            raise ValueError(f"run start failed: {_problem_context(error)}") from None
        refreshed_runs = _read_cycle_runs(
            base_url=base_url,
            project_id=project_id,
            cycle_id=cycle_id,
            token=token,
            requester=requester,
        )
        refreshed = next(
            (run for run in refreshed_runs if run.get(FIELD_ID) == run_id), None
        )
        if refreshed is None:
            raise ValueError("run disappeared after revision conflict") from None
        if refreshed.get(FIELD_STATUS) == "IN_PROGRESS":
            return refreshed
        revision = _revision(refreshed, "planned run")
        started = requester(
            url,
            token,
            method=HTTP_POST,
            key=command_key(pipeline_run_id, "run", run_id, COMMAND_START, revision, 2),
            if_match=f'"{revision}"',
        )
    if started.get(FIELD_STATUS) != "IN_PROGRESS":
        raise ValueError("run start did not return an IN_PROGRESS run")
    return started


def _select_cycle(
    cycles: list[dict[str, Any]], configured_id: str, cycle_name: str
) -> dict[str, Any] | None:
    if configured_id:
        selected = next(
            (cycle for cycle in cycles if cycle.get(FIELD_ID) == configured_id), None
        )
        if selected is None:
            raise ValueError("configured cycle is not visible in the project")
        return selected
    reusable = [
        cycle
        for cycle in cycles
        if cycle.get(FIELD_NAME) == cycle_name
        and cycle.get(FIELD_STATUS) in {STATUS_DRAFT, "ACTIVE"}
    ]
    reusable.sort(key=lambda cycle: cycle.get(FIELD_STATUS) != "ACTIVE")
    return reusable[0] if reusable else None


def _create_cycle(
    url: str, token: str, pipeline_run_id: str, requester
) -> dict[str, Any]:
    payload = {
        FIELD_NAME: "Apistra CAP-00 Reporting",
        "objective": (
            "Authenticated CI report write/read round-trips and receipt evidence "
            "for the CAP-00 delivery gate."
        ),
        "build": "CAP-00",
        "environment": LOCAL_PIPELINE_ID,
    }
    selected = requester(
        url,
        token,
        method=HTTP_POST,
        key=command_key(
            pipeline_run_id,
            RESOURCE_CYCLE,
            "cap00-integration",
            COMMAND_CREATE,
            "none",
            1,
        ),
        payload=payload,
    )
    if not selected.get(FIELD_ID):
        raise ValueError("cycle create response has no id")
    return selected


def _add_cycle_item(
    url: str,
    token: str,
    selected: dict[str, Any],
    anchor_version_id: str,
    pipeline_run_id: str,
    requester,
) -> dict[str, Any]:
    cycle_id = str(selected[FIELD_ID])
    revision = _revision(selected, DRAFT_CYCLE_LABEL)
    item_url = f"{url}/{cycle_id}/items"
    try:
        requester(
            item_url,
            token,
            method=HTTP_POST,
            key=command_key(
                pipeline_run_id, RESOURCE_CYCLE, cycle_id, "add-item", revision, 1
            ),
            if_match=f'"{revision}"',
            payload={"version_id": anchor_version_id},
        )
    except ApiError as error:
        if error.code != "REVISION_CONFLICT":
            raise ValueError(
                f"cycle item creation failed: {_problem_context(error)}"
            ) from None
        selected = _refresh_cycle(url, token, cycle_id, requester)
        if selected.get("run_count", 0) < 1:
            revision = _revision(selected, DRAFT_CYCLE_LABEL)
            requester(
                item_url,
                token,
                method=HTTP_POST,
                key=command_key(
                    pipeline_run_id, RESOURCE_CYCLE, cycle_id, "add-item", revision, 2
                ),
                if_match=f'"{revision}"',
                payload={"version_id": anchor_version_id},
            )
    return _refresh_cycle(url, token, cycle_id, requester)


def _ensure_cycle_item(
    url: str,
    token: str,
    selected: dict[str, Any],
    anchor_version_id: str,
    pipeline_run_id: str,
    requester,
) -> dict[str, Any]:
    needs_item = (
        selected.get(FIELD_STATUS) == STATUS_DRAFT and selected.get("run_count", 0) < 1
    )
    if not needs_item:
        return selected
    if not anchor_version_id:
        raise ValueError(
            "draft cycle has no planned run; SOFTWARETEST_ANCHOR_VERSION_ID is required"
        )
    return _add_cycle_item(
        url,
        token,
        selected,
        anchor_version_id,
        pipeline_run_id,
        requester,
    )


def _start_cycle(
    url: str,
    token: str,
    selected: dict[str, Any],
    pipeline_run_id: str,
    requester,
) -> dict[str, Any]:
    if selected.get(FIELD_STATUS) != STATUS_DRAFT:
        return selected
    if selected.get("run_count", 0) < 1:
        raise ValueError("draft cycle still has no executable planned run")
    cycle_id = str(selected[FIELD_ID])
    revision = _revision(selected, DRAFT_CYCLE_LABEL)
    start_url = f"{url}/{cycle_id}:start"
    try:
        return requester(
            start_url,
            token,
            method=HTTP_POST,
            key=command_key(
                pipeline_run_id, RESOURCE_CYCLE, cycle_id, COMMAND_START, revision, 1
            ),
            if_match=f'"{revision}"',
        )
    except ApiError as error:
        if error.code == "CYCLE_START_PRECONDITION_FAILED":
            raise ValueError(
                f"cycle start precondition failed: {_problem_context(error)}"
            ) from None
        if error.code != "REVISION_CONFLICT":
            raise ValueError(f"cycle start failed: {_problem_context(error)}") from None
    refreshed = _refresh_cycle(url, token, cycle_id, requester)
    if refreshed.get(FIELD_STATUS) != STATUS_DRAFT:
        return refreshed
    revision = _revision(refreshed, DRAFT_CYCLE_LABEL)
    return requester(
        start_url,
        token,
        method=HTTP_POST,
        key=command_key(
            pipeline_run_id, RESOURCE_CYCLE, cycle_id, COMMAND_START, revision, 2
        ),
        if_match=f'"{revision}"',
    )


def ensure_cycle(
    *,
    base_url: str,
    project_id: str,
    token: str,
    configured_id: str = "",
    anchor_version_id: str = "",
    pipeline_run_id: str = LOCAL_PIPELINE_ID,
    requester=request_json,
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    """Return an active CAP-00 cycle and its started execution run."""
    url = f"{base_url}/api/v1/projects/{project_id}/cycles"
    page = requester(url, token, method=HTTP_GET)
    selected = _select_cycle(
        page.get(FIELD_RESULTS, []), configured_id, "Apistra CAP-00 Reporting"
    )
    created_cycle = selected is None
    if selected is None:
        selected = _create_cycle(url, token, pipeline_run_id, requester)

    selected = _ensure_cycle_item(
        url, token, selected, anchor_version_id, pipeline_run_id, requester
    )
    selected = _start_cycle(url, token, selected, pipeline_run_id, requester)
    if selected.get(FIELD_STATUS) != "ACTIVE":
        raise ValueError("CAP-00 cycle is not active")
    run = _start_cycle_run(
        base_url=base_url,
        project_id=project_id,
        cycle_id=str(selected[FIELD_ID]),
        token=token,
        pipeline_run_id=pipeline_run_id,
        requester=requester,
    )
    return selected, created_cycle, run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--outbox", type=Path, default=Path("artifacts/softwaretest-outbox.json")
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("artifacts/softwaretest-roundtrip-receipt.json"),
    )
    parser.add_argument(
        "--ensure-cycle",
        action="store_true",
        help="Reuse or idempotently create the dedicated CAP-00 test cycle.",
    )
    parser.add_argument(
        "--command-revision",
        default="ci-guide-1.1-stage-v2",
        help="Rotate idempotency keys after a rejected command contract changes.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    token = os.getenv("SOFTWARETEST_TOKEN", "")
    project_id = os.getenv("SOFTWARETEST_PROJECT_ID", "")
    base_url = (os.getenv("SOFTWARETEST_BASE_URL") or "https://softwaretest.it").rstrip(
        "/"
    )
    cycle_id = os.getenv("SOFTWARETEST_CYCLE_ID", "")
    anchor_version_id = os.getenv("SOFTWARETEST_ANCHOR_VERSION_ID", "")
    cycle_evidence: dict[str, Any] = {}
    if args.apply and token and project_id and args.ensure_cycle:
        try:
            cycle, created, run = ensure_cycle(
                base_url=base_url,
                project_id=project_id,
                token=token,
                configured_id=cycle_id,
                anchor_version_id=anchor_version_id,
                pipeline_run_id=str(bundle.get("pipeline_id", LOCAL_PIPELINE_ID)),
            )
            cycle_id = cycle[FIELD_ID]
            cycle_evidence = {"created": created, "document": cycle, "run": run}
        except (
            ApiError,
            OSError,
            urllib.error.URLError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as error:
            write_failure_receipt(
                args.receipt,
                project_id=project_id,
                base_url=base_url,
                token=token,
                command_revision=args.command_revision,
                stage=RESOURCE_CYCLE,
                error=error,
            )
            detail = str(error) or type(error).__name__
            print(
                "Cycle preparation failed safely; failure receipt retained at "
                f"{args.receipt}: {detail}"
            )
            return 1
    effective_cycle_id = cycle_id or "BLOCKED-AUTHORISED-CYCLE-REQUIRED"
    report, entries, final = build_payloads(bundle, effective_cycle_id)
    outbox = {
        "report": report,
        FIELD_ENTRIES: {FIELD_ENTRIES: entries},
        COMMAND_FINALIZE: final,
    }
    write_json_atomic(args.outbox, redact(outbox, (token,)))
    if not args.apply:
        print(f"Dry run: lossless redacted outbox written to {args.outbox}")
        return 0
    if not token or not project_id or cycle_id.startswith("BLOCKED-"):
        print(
            "BLOCKED: protected Softwaretest.it token, project and cycle are required"
        )
        return 2
    try:
        result = execute_roundtrip(
            base_url=base_url,
            project_id=project_id,
            token=token,
            report=report,
            entries=entries,
            final=final,
            command_revision=args.command_revision,
        )
        evidence = {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "project_id": project_id,
            "base_url": base_url,
            RESOURCE_CYCLE: cycle_evidence,
            "command_revision": args.command_revision,
            **result,
        }
        write_json_atomic(args.receipt, redact(evidence, (token,)))
        if not result["verified"]:
            print(f"Readback mismatch; receipt retained at {args.receipt}")
            return 1
        print(
            f"Softwaretest.it report {result['report_id']} published, read back, "
            f"and verified. Receipt: {args.receipt}"
        )
        return 0
    except (
        OSError,
        urllib.error.URLError,
        json.JSONDecodeError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        write_failure_receipt(
            args.receipt,
            project_id=project_id,
            base_url=base_url,
            token=token,
            command_revision=args.command_revision,
            stage="report",
            error=error,
            cycle=cycle_evidence,
            request_sha256={
                COMMAND_CREATE: payload_sha256(report),
                FIELD_ENTRIES: payload_sha256({FIELD_ENTRIES: entries}),
                COMMAND_FINALIZE: payload_sha256(final),
            },
        )
        detail = str(error) or type(error).__name__
        print(f"Reporting failed safely; outbox and failure receipt retained: {detail}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
