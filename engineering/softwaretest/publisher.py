"""Lossless CAP-00 CI-report publisher with dry-run default and redaction."""

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


def stable_key(prefix: str, value: str) -> str:
    return f"apistra-cap00-{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:24]}"


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
    url: str, token: str, key: str, payload: dict[str, Any]
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Idempotency-Key": key,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--outbox", type=Path, default=Path("artifacts/softwaretest-outbox.json")
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    cycle_id = os.getenv("SOFTWARETEST_CYCLE_ID", "BLOCKED-AUTHORISED-CYCLE-REQUIRED")
    report, entries, final = build_payloads(bundle, cycle_id)
    token = os.getenv("SOFTWARETEST_TOKEN", "")
    project_id = os.getenv("SOFTWARETEST_PROJECT_ID", "")
    base_url = os.getenv("SOFTWARETEST_BASE_URL", "https://softwaretest.it").rstrip("/")
    outbox = {"report": report, "entries": {"entries": entries}, "finalize": final}
    args.outbox.parent.mkdir(parents=True, exist_ok=True)
    args.outbox.write_text(
        json.dumps(redact(outbox, (token,)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not args.apply:
        print(f"Dry run: lossless redacted outbox written to {args.outbox}")
        return 0
    if not token or not project_id or cycle_id.startswith("BLOCKED-"):
        print(
            "BLOCKED: protected Softwaretest.it token, project and cycle are required"
        )
        return 2
    try:
        root = f"{base_url}/api/v1/projects/{project_id}/ci-reports"
        receipt = request_json(
            root, token, stable_key("create", report["external_key"]), report
        )
        report_id = receipt.get("report_id") or receipt.get("id")
        if not report_id:
            print("Create response has no report identifier; outbox retained")
            return 1
        request_json(
            f"{root}/{report_id}/entries",
            token,
            stable_key("entries", report["external_key"]),
            {"entries": entries},
        )
        request_json(
            f"{root}/{report_id}/finalize",
            token,
            stable_key("finalize", report["external_key"]),
            final,
        )
        print(f"Softwaretest.it report {report_id} published and finalised.")
        return 0
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Reporting failed safely; outbox retained: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
