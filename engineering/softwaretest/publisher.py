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

ALLOWED_STATUSES = {"PASSED", "FAILED", "SKIPPED", "ERROR", "CANCELLED"}


class ApiError(RuntimeError):
    """Sanitised API failure containing no request headers or credentials."""

    def __init__(self, status: int, problem: dict[str, Any]) -> None:
        self.status = status
        self.problem_type = str(problem.get("type", ""))[:200]
        self.title = str(problem.get("title", ""))[:200]
        self.detail = str(problem.get("detail", ""))[:500]
        summary = self.title or self.problem_type or "API request failed"
        if self.detail:
            summary = f"{summary}: {self.detail}"
        super().__init__(f"HTTP {status} {summary}")


def stable_key(prefix: str, value: str) -> str:
    return f"apistra-cap00-{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:24]}"


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


def build_payloads(
    bundle: dict[str, Any], cycle_id: str
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    now = datetime.now(UTC).isoformat()
    candidate = bundle["candidate"]
    results = bundle["results"]
    statuses = {result["status"] for result in results}
    unsupported = statuses - ALLOWED_STATUSES
    if unsupported:
        raise ValueError(f"unsupported result statuses: {sorted(unsupported)}")
    report = {
        "cycle_id": cycle_id,
        "external_key": f"cap00-{candidate['commit']}",
        "pipeline_id": bundle.get("pipeline_id", "local"),
        "job_id": bundle.get("job_id", "cap00-candidate"),
        "commit_sha": candidate["commit"],
        "artifact_digest": candidate["manifest_sha256"],
        "started_at": bundle.get("started_at", now),
        "contract_version": "1.0",
        "source_repository": "Apistra/Apistra",
        "capability_ids": ["CAP-00"],
        "workorder_ids": [f"WO-CAP-00-{index:02d}" for index in range(1, 8)],
        "required_stages": [
            {
                "stage_id": "cap00",
                "job_id": "cap00-candidate",
                "expected_tests": len(results),
                "required": True,
            }
        ],
    }
    entries = [
        {
            "kind": "test",
            "stage_id": "cap00",
            "job_id": "cap00-candidate",
            "suite": result.get("suite", "cap00"),
            "test_id": result["test_id"],
            "name": result.get("name", result["test_id"]),
            "attempt_no": result.get("attempt_no", 1),
            "status": result["status"],
            "started_at": result.get("started_at", now),
            "finished_at": result.get("finished_at", now),
            "duration_ms": int(result.get("duration_ms", 0)),
            "error_details": result.get("error_details", ""),
            "metrics": result.get("metrics", []),
            "findings": result.get("findings", []),
            "attachments": result.get("attachments", []),
        }
        for result in results
    ]
    return report, entries, {"finished_at": bundle.get("finished_at", now)}


def request_json(
    url: str,
    token: str,
    *,
    method: str = "GET",
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
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            problem = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            problem = {}
        raise ApiError(error.code, problem) from None


def _compare_requested(
    expected: Any, actual: Any, path: str, mismatches: list[str]
) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            mismatches.append(f"{path}: expected object")
            return
        for key, value in expected.items():
            if key not in actual:
                mismatches.append(f"{path}.{key}: missing")
            else:
                _compare_requested(value, actual[key], f"{path}.{key}", mismatches)
        return
    if isinstance(expected, list):
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
        return
    if (
        isinstance(expected, str)
        and isinstance(actual, str)
        and path.endswith(("started_at", "finished_at"))
    ):
        try:
            expected_time = datetime.fromisoformat(expected.replace("Z", "+00:00"))
            actual_time = datetime.fromisoformat(actual.replace("Z", "+00:00"))
            if expected_time == actual_time:
                return
        except ValueError:
            pass
    if expected != actual:
        mismatches.append(f"{path}: value differs")


def verify_readback(
    report: dict[str, Any], entries: list[dict[str, Any]], document: dict[str, Any]
) -> list[str]:
    """Compare every submitted field while allowing server-owned response fields."""
    mismatches: list[str] = []
    _compare_requested(report, document.get("manifest"), "manifest", mismatches)
    _compare_requested(entries, document.get("entries"), "entries", mismatches)
    if str(document.get("status", "")).upper() not in {"FINALIZED", "COMPLETE"}:
        mismatches.append("status: report is not finalised")
    return mismatches


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


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
        ("create", root, report),
        ("entries", "", {"entries": entries}),
        ("finalize", "", final),
    )
    receipts: dict[str, Any] = {}
    report_id = ""
    for command, configured_url, payload in commands:
        url = configured_url or f"{root}/{report_id}/{command}"
        try:
            response = requester(
                url,
                token,
                method="POST",
                key=stable_key(command, f"{external_key}:{command_revision}"),
                payload=payload,
            )
        except ApiError as error:
            raise RuntimeError(f"{command} request returned {error}") from None
        if command == "create":
            report_id = response.get("report_id", "")
            if not report_id:
                raise ValueError("create response has no report_id")
        if response.get("report_id") != report_id:
            raise ValueError(f"{command} receipt references another report")
        receipts[command] = response

    try:
        document = requester(f"{root}/{report_id}", token, method="GET")
    except ApiError as error:
        raise RuntimeError(f"report readback returned {error}") from None
    if document.get("report_id") != report_id:
        raise ValueError("readback references another report")
    mismatches = verify_readback(report, entries, document)

    receipt_documents: dict[str, Any] = {}
    receipt_root = f"{base_url}/api/v1/projects/{project_id}/reporting-receipts"
    for command, receipt in receipts.items():
        receipt_id = receipt.get("receipt_id")
        if receipt_id:
            try:
                receipt_documents[command] = requester(
                    f"{receipt_root}/{receipt_id}", token, method="GET"
                )
            except ApiError as error:
                raise RuntimeError(
                    f"{command} receipt readback returned {error}"
                ) from None

    return {
        "report_id": report_id,
        "verified": not mismatches,
        "mismatches": mismatches,
        "request_sha256": {
            "create": payload_sha256(report),
            "entries": payload_sha256({"entries": entries}),
            "finalize": payload_sha256(final),
        },
        "server_receipts": receipts,
        "receipt_readbacks": receipt_documents,
        "report_readback": document,
    }


def ensure_cycle(
    *,
    base_url: str,
    project_id: str,
    token: str,
    configured_id: str = "",
    anchor_version_id: str = "",
    requester=request_json,
) -> tuple[dict[str, Any], bool]:
    """Return a configured or reusable CAP-00 cycle, creating it idempotently."""
    url = f"{base_url}/api/v1/projects/{project_id}/cycles"
    cycle_name = "Apistra CAP-00 Reporting"
    page = requester(url, token, method="GET")
    cycles = page.get("results", [])
    selected: dict[str, Any] | None = None
    created_cycle = False
    if configured_id:
        for cycle in cycles:
            if cycle.get("id") == configured_id:
                selected = cycle
                break
        if selected is None:
            raise ValueError("configured cycle is not visible in the project")
    else:
        reusable = [
            cycle
            for cycle in cycles
            if cycle.get("name") == cycle_name
            and cycle.get("status") in {"DRAFT", "ACTIVE"}
        ]
        if reusable:
            reusable.sort(key=lambda cycle: cycle.get("status") != "ACTIVE")
            selected = reusable[0]

    if selected is None:
        payload = {
            "name": cycle_name,
            "objective": (
                "Authenticated CI report write/read round-trips and receipt evidence "
                "for the CAP-00 delivery gate."
            ),
            "build": "CAP-00",
            "environment": "local",
        }
        selected = requester(
            url,
            token,
            method="POST",
            key=stable_key("cycle", f"{project_id}:cap00-integration"),
            payload=payload,
        )
        created_cycle = True
        if not selected.get("id"):
            raise ValueError("cycle create response has no id")

    if selected.get("status") == "DRAFT" and selected.get("run_count", 0) < 1:
        if not anchor_version_id:
            raise ValueError(
                "draft cycle has no planned run; SOFTWARETEST_ANCHOR_VERSION_ID "
                "is required"
            )
        revision = selected.get("revision")
        if not isinstance(revision, int):
            raise ValueError("draft cycle has no revision")
        requester(
            f"{url}/{selected['id']}/items",
            token,
            method="POST",
            key=stable_key("cycle-item", f"{selected['id']}:{anchor_version_id}"),
            if_match=f'"{revision}"',
            payload={"version_id": anchor_version_id},
        )
        refreshed_page = requester(url, token, method="GET")
        selected = next(
            (
                cycle
                for cycle in refreshed_page.get("results", [])
                if cycle.get("id") == selected["id"]
            ),
            None,
        )
        if selected is None:
            raise ValueError("planned cycle disappeared from project listing")

    if selected.get("status") == "DRAFT":
        if selected.get("run_count", 0) < 1:
            raise ValueError("draft cycle still has no executable planned run")
        revision = selected.get("revision")
        if not isinstance(revision, int):
            raise ValueError("draft cycle has no revision")
        selected = requester(
            f"{url}/{selected['id']}:start",
            token,
            method="POST",
            key=stable_key("cycle-start", f"{selected['id']}:{revision}"),
            if_match=f'"{revision}"',
        )
    if selected.get("status") != "ACTIVE":
        raise ValueError("CAP-00 cycle is not active")
    return selected, created_cycle


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
        default="v1",
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
            cycle, created = ensure_cycle(
                base_url=base_url,
                project_id=project_id,
                token=token,
                configured_id=cycle_id,
                anchor_version_id=anchor_version_id,
            )
            cycle_id = cycle["id"]
            cycle_evidence = {"created": created, "document": cycle}
        except (
            ApiError,
            OSError,
            urllib.error.URLError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            print(f"Cycle resolution failed safely: {type(error).__name__}")
            return 1
    effective_cycle_id = cycle_id or "BLOCKED-AUTHORISED-CYCLE-REQUIRED"
    report, entries, final = build_payloads(bundle, effective_cycle_id)
    outbox = {"report": report, "entries": {"entries": entries}, "finalize": final}
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
            "cycle": cycle_evidence,
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
        ValueError,
    ) as error:
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(f"Reporting failed safely; outbox retained: {detail}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
