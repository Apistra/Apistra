"""Publish canonical Capability and Workorder sources to Softwaretest.it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from publisher import (
    ApiError,
    canonical_datetime,
    payload_sha256,
    redact,
    request_json,
    write_json_atomic,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAPABILITY_DIR = ROOT / "docs/capabilities"
DEFAULT_WORKORDER_DIR = ROOT / "docs/workorders"
DEFAULT_OUTBOX = ROOT / "artifacts/softwaretest-steering-outbox.json"
DEFAULT_RECEIPT = ROOT / "artifacts/softwaretest-steering-receipt.json"
SOURCE = "apistra-spec-to-workorders"
CONTRACT_VERSION = "1.0"
CANONICAL_BRANCH = "test"
REPOSITORY_URL = "https://github.com/Apistra/Apistra"
HTTP_POST = "POST"
TYPE_CAPABILITY = "CAPABILITY"
TYPE_WORKORDER = "WORKORDER"
FIELD_EXTERNAL_ID = "external_id"
FIELD_TITLE = "title"
FIELD_CONTENT_SHA256 = "content_sha256"
FIELD_PAYLOAD = "payload"
FIELD_SOURCE = "source"
FIELD_ITEMS = "items"
FIELD_PAYLOAD_SHA256 = "payload_sha256"
FIELD_PAYLOAD_HASH_CONTRACT = "payload_hash_contract"
FIELD_CRITERIA = "criteria"
FIELD_STATUS = "status"
FIELD_DUE_NOW = "due_now"
FIELD_GATE = "gate"
FIELD_REASON = "reason"
STATUS_PLANNED = "PLANNED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_IMPLEMENTED = "IMPLEMENTED"
STATUS_BLOCKED = "BLOCKED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_OPEN = "OPEN"
STATUS_APPROVED = "APPROVED"
STATUS_EVIDENCE_MISSING = "MISSING"
STATUS_EVIDENCE_PARTIAL = "PARTIAL"
STATUS_EVIDENCE_CURRENT = "CURRENT"
STATUS_EVIDENCE_FAILED = "FAILED"
STATUS_EVIDENCE_STALE = "STALE"
STATUS_PENDING = "PENDING"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_NOT_REQUIRED = "NOT_REQUIRED"
CRITERION_PASSED = "PASSED"
CRITERION_UNKNOWN = "UNKNOWN"
SOURCE_STATUS_FINAL_ACCEPTANCE_READY = "FINAL ACCEPTANCE READY"
STEERING_EVIDENCE_STATUSES = frozenset(
    {
        STATUS_EVIDENCE_MISSING,
        STATUS_EVIDENCE_PARTIAL,
        STATUS_EVIDENCE_CURRENT,
        STATUS_EVIDENCE_FAILED,
        STATUS_EVIDENCE_STALE,
        STATUS_UNKNOWN,
    }
)
MAX_IMPORT_ITEMS = 100
MAX_TITLE_LENGTH = 240
MAX_CRITERION_LENGTH = 300
MAX_GATE_LENGTH = 120
MAX_GOAL_LENGTH = 10_000
MAX_NON_GOAL_LENGTH = 1_000
MAX_DELTA_LENGTH = 10_000
MAX_NEXT_STEP_LENGTH = 500
VERSION_MAJOR_SCALE = 1_000_000
VERSION_MINOR_SCALE = 1_000
SOURCE_REVISION_SCALE = 100
# Bump whenever mapping changes alter imported content without a document version bump.
PROJECTION_REVISION = 3
MAX_SOURCE_REVISION = 2_147_483_647
CONTENT_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CURRENT_PAYLOAD_HASH_CONTRACT = "rfc8785-sha256"
LEGACY_PAYLOAD_HASH_CONTRACT = "legacy-drf-normalized-sha256"
MAX_IJSON_INTEGER = 9_007_199_254_740_991
DATETIME_FIELDS = frozenset({"observed_at", "confirmed_at"})
HEADING_PATTERN = re.compile(
    r"^# (?P<id>CAP-\d{2}|WO-CAP-\d{2}-\d{2}) — (?P<title>.+)$"
)
VERSION_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?")
IDENTIFIER_PATTERN = re.compile(r"\b(?:WO-)?CAP-\d{2}(?:-\d{2})?\b")
NUMBERED_ITEM_PATTERN = re.compile(r"^\d+\.\s+(.+)$")
CRITERION_STATE_PATTERN = re.compile(
    r"^- (?P<id>(?:WO-)?CAP-\d{2}(?:-\d{2})?-AC-\d{2}): "
    r"status=(?P<status>PASSED|NOT_APPLICABLE|UNKNOWN); "
    r"due_now=(?P<due_now>true|false); "
    r"gate=(?P<gate>[^;]*); reason=(?P<reason>.+)$"
)
SNAPSHOT_PATTERN = re.compile(
    r"implementation snapshot:\s*`([0-9a-f]{7,40})`",
    re.IGNORECASE,
)

ObservedAtProvider = Callable[[Path], str]
Requester = Callable[..., dict[str, Any]]


class SteeringPublishError(RuntimeError):
    """Retain safe progress evidence when a batched publish fails."""

    def __init__(
        self,
        phase: str,
        cause: Exception,
        completed_batches: list[dict[str, Any]],
        *,
        batch_number: int | None = None,
        failed_receipt: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(str(cause))
        self.phase = phase
        self.cause = cause
        self.completed_batches = completed_batches
        self.batch_number = batch_number
        self.failed_receipt = failed_receipt


def _metadata(text: str, name: str, *, required: bool = True) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    if required:
        raise ValueError(f"missing metadata: {name}")
    return ""


def _section(text: str, *headings: str) -> str:
    for heading in headings:
        pattern = re.compile(
            rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group("body").strip()
    return ""


def _normalise(value: str) -> str:
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def _bullet_items(section: str) -> list[str]:
    return [
        line.removeprefix("- ").strip()
        for line in section.splitlines()
        if line.startswith("- ")
    ]


def _numbered_items(section: str) -> list[str]:
    items: list[str] = []
    current = ""
    for raw_line in section.splitlines():
        line = raw_line.strip()
        match = NUMBERED_ITEM_PATTERN.match(line)
        if match:
            if current:
                items.append(current)
            current = match.group(1).strip()
        elif line and current:
            current = f"{current} {line}"
    if current:
        items.append(current)
    return items


def _source_revision(version: str) -> int:
    match = VERSION_PATTERN.match(version)
    if not match:
        raise ValueError(f"unsupported source version: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch") or 0)
    document_revision = (
        major * VERSION_MAJOR_SCALE + minor * VERSION_MINOR_SCALE + patch + 1
    )
    source_revision = document_revision * SOURCE_REVISION_SCALE + PROJECTION_REVISION
    if source_revision > MAX_SOURCE_REVISION:
        raise ValueError(f"source revision exceeds API limit: {version}")
    return source_revision


def _implementation_status(status: str) -> str:
    normalised = status.upper()
    if normalised.startswith(("DRAFT", "READY")):
        return STATUS_PLANNED
    if normalised.startswith(
        ("DONE", "ACCEPTED", SOURCE_STATUS_FINAL_ACCEPTANCE_READY)
    ):
        return STATUS_IMPLEMENTED
    if normalised.startswith("BLOCKED"):
        return STATUS_BLOCKED
    if (
        normalised.startswith("IN_PROGRESS")
        or "FINAL ACCEPTANCE PREPARATION" in normalised
    ):
        return STATUS_IN_PROGRESS
    raise ValueError(f"unsupported implementation status: {status}")


def _approval_status(status: str, approval: str) -> str:
    combined = f"{status}; {approval}".upper()
    if any(
        marker in combined
        for marker in ("NOT APPROVED", "NOT YET APPROVED", "NOT ACCEPTED")
    ):
        return STATUS_OPEN
    if any(
        marker in combined
        for marker in (
            "HUMAN ACCEPTED",
            "IMPLEMENTATION AUTHORISED",
            "APPROVED",
            "REVIEWED",
            "REVIEW COMPLETE",
            "RESULT VERIFIED",
        )
    ):
        return STATUS_APPROVED
    if status.upper().startswith("ACCEPTED"):
        return STATUS_APPROVED
    return STATUS_UNKNOWN


def _evidence_status(evidence: str) -> str:
    normalised = evidence.upper()
    if not normalised or normalised.startswith("NOT EXECUTED"):
        return STATUS_EVIDENCE_MISSING
    if "FAILED" in normalised:
        return STATUS_EVIDENCE_FAILED
    if "STALE" in normalised:
        return STATUS_EVIDENCE_STALE
    if "NOT EXECUTED" in normalised:
        return STATUS_EVIDENCE_PARTIAL
    if "VERIFIED" in normalised or "COMPLETE FOR THIS WORKORDER" in normalised:
        return STATUS_EVIDENCE_CURRENT
    return STATUS_UNKNOWN


def _transmission_status(text: str) -> str:
    mapping = re.search(r"^- Softwaretest\.it mapping:\s*(.+)$", text, re.MULTILINE)
    if not mapping:
        return STATUS_UNKNOWN
    value = mapping.group(1).upper()
    # This source field describes the workorder's test-definition/reporting
    # obligation, not the receipt for the Steering import being performed now.
    if "NOT PUBLISHED; ASSIGNED TO" in value:
        return STATUS_NOT_REQUIRED
    if "NOT PUBLISHED" in value or "PARTIAL" in value:
        return STATUS_PENDING
    if "PUBLISHED" in value or "TESTCASES" in value:
        return STATUS_CONFIRMED
    return STATUS_UNKNOWN


def _dependencies(text: str, external_id: str) -> list[str]:
    relevant = "\n".join(
        (
            _section(text, "Prerequisites"),
            _section(text, "Actors and prerequisites"),
            _section(text, "Dependencies and follow-up"),
        )
    )
    return sorted(set(IDENTIFIER_PATTERN.findall(relevant)) - {external_id})


def _delta(text: str) -> str:
    match = re.search(r"^- Delta:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _next_step(text: str) -> str:
    match = re.search(r"^\*\*Next step:\*\*\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _candidate(text: str) -> str:
    match = SNAPSHOT_PATTERN.search(text)
    return match.group(1) if match else ""


def git_observed_at(path: Path) -> str:
    relative_path = path.relative_to(ROOT).as_posix()
    command = ("git", "log", "-1", "--format=%cI", "--", relative_path)
    # The executable and every option are fixed; only the repository-relative path varies.
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    observed_at = completed.stdout.strip()
    if not observed_at:
        raise ValueError(f"no Git observation timestamp for {relative_path}")
    return canonical_datetime(observed_at)


def _criterion_states(text: str, external_id: str) -> dict[str, dict[str, Any]]:
    section = _section(text, "Steering criterion evidence")
    if not section:
        return {}
    states: dict[str, dict[str, Any]] = {}
    for line in section.splitlines():
        if not line.strip():
            continue
        match = CRITERION_STATE_PATTERN.fullmatch(line.strip())
        if not match:
            raise ValueError(f"invalid Steering criterion evidence: {line.strip()}")
        criterion_id = match.group("id")
        if not criterion_id.startswith(f"{external_id}-AC-"):
            raise ValueError(
                f"criterion evidence belongs to another source: {criterion_id}"
            )
        if criterion_id in states:
            raise ValueError(f"duplicate criterion evidence: {criterion_id}")
        states[criterion_id] = {
            FIELD_STATUS: match.group(FIELD_STATUS),
            FIELD_DUE_NOW: match.group(FIELD_DUE_NOW) == "true",
            FIELD_GATE: match.group(FIELD_GATE).strip(),
            FIELD_REASON: match.group(FIELD_REASON).strip(),
        }
    return states


def _criteria(text: str, external_id: str) -> list[dict[str, Any]]:
    titles = _numbered_items(_section(text, "Acceptance criteria"))
    states = _criterion_states(text, external_id)
    criteria = []
    for index, title in enumerate(titles, 1):
        criterion_id = f"{external_id}-AC-{index:02d}"
        state = states.pop(criterion_id, {})
        criteria.append(
            {
                FIELD_EXTERNAL_ID: criterion_id,
                FIELD_TITLE: title,
                FIELD_STATUS: state.get(FIELD_STATUS, CRITERION_UNKNOWN),
                "required": True,
                FIELD_DUE_NOW: state.get(FIELD_DUE_NOW, False),
                "exception_allowed": False,
                FIELD_GATE: state.get(FIELD_GATE, ""),
                FIELD_REASON: state.get(FIELD_REASON, ""),
            }
        )
    if states:
        raise ValueError(
            f"criterion evidence has no acceptance criterion: {min(states)}"
        )
    return criteria


def _source_url(relative_path: str) -> str:
    return f"{REPOSITORY_URL}/blob/{CANONICAL_BRANCH}/{relative_path}"


def _validate_lengths(item: dict[str, Any]) -> None:
    limits = {
        FIELD_TITLE: MAX_TITLE_LENGTH,
        "goal": MAX_GOAL_LENGTH,
        "delta": MAX_DELTA_LENGTH,
        "next_step": MAX_NEXT_STEP_LENGTH,
    }
    for field, limit in limits.items():
        if len(item[field]) > limit:
            raise ValueError(f"{item[FIELD_EXTERNAL_ID]} {field} exceeds API limit")
    if any(len(value) > MAX_NON_GOAL_LENGTH for value in item["non_goals"]):
        raise ValueError(f"{item[FIELD_EXTERNAL_ID]} non-goal exceeds API limit")
    if any(
        len(value[FIELD_TITLE]) > MAX_CRITERION_LENGTH for value in item[FIELD_CRITERIA]
    ):
        raise ValueError(f"{item[FIELD_EXTERNAL_ID]} criterion exceeds API limit")
    if any(len(value[FIELD_GATE]) > MAX_GATE_LENGTH for value in item[FIELD_CRITERIA]):
        raise ValueError(f"{item[FIELD_EXTERNAL_ID]} criterion gate exceeds API limit")
    if any(len(value[FIELD_REASON]) > 1_000 for value in item[FIELD_CRITERIA]):
        raise ValueError(
            f"{item[FIELD_EXTERNAL_ID]} criterion reason exceeds API limit"
        )


def parse_source(path: Path, observed_at: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    heading = HEADING_PATTERN.match(text.splitlines()[0])
    if not heading:
        raise ValueError(f"invalid steering source heading: {path}")
    external_id = heading.group("id")
    source_type = TYPE_WORKORDER if external_id.startswith("WO-") else TYPE_CAPABILITY
    relative_path = path.relative_to(ROOT).as_posix()
    status = _metadata(text, "Status")
    implementation_status = _implementation_status(status)
    goal = _section(text, "Target result", "Goal and value")
    item = {
        FIELD_EXTERNAL_ID: external_id,
        "source_revision": _source_revision(_metadata(text, "Version")),
        "type": source_type,
        FIELD_TITLE: heading.group(FIELD_TITLE).strip(),
        "source_url": _source_url(relative_path),
        "goal": _normalise(goal),
        "non_goals": _bullet_items(
            _section(text, "Non-goals", "Non-goals and prohibited side effects")
        ),
        "risk_profile": _metadata(text, "Assurance"),
        "delta": _delta(text),
        "dependencies": _dependencies(text, external_id),
        "candidate": _candidate(text),
        "environment": "",
        "implementation_status": implementation_status,
        "evidence_status": _evidence_status(
            _metadata(text, "Evidence state", required=False)
        ),
        "transmission_status": _transmission_status(text),
        "approval_status": _approval_status(
            status,
            _metadata(text, "Approval state", required=False),
        ),
        "responsible_role": "",
        "next_step": _next_step(text),
        "due_gate": "",
        "observed_at": canonical_datetime(observed_at),
        "confirmed_at": None,
        FIELD_CRITERIA: _criteria(text, external_id),
        "decisions": [],
    }
    _validate_lengths(item)
    return {
        "source_path": relative_path,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        FIELD_CONTENT_SHA256: payload_sha256(item),
        FIELD_PAYLOAD: item,
    }


def build_manifest(
    capability_dir: Path = DEFAULT_CAPABILITY_DIR,
    workorder_dir: Path = DEFAULT_WORKORDER_DIR,
    observed_at_provider: ObservedAtProvider = git_observed_at,
) -> dict[str, Any]:
    paths = [
        *sorted(capability_dir.glob("CAP-*.md")),
        *sorted(workorder_dir.glob("CAP-*/WO-CAP-*.md")),
    ]
    sources = [parse_source(path, observed_at_provider(path)) for path in paths]
    payload = {
        "contract_version": CONTRACT_VERSION,
        FIELD_SOURCE: SOURCE,
        FIELD_ITEMS: [source[FIELD_PAYLOAD] for source in sources],
    }
    manifest = {
        "schema_version": CONTRACT_VERSION,
        FIELD_SOURCE: SOURCE,
        "capability_count": sum(
            source[FIELD_PAYLOAD]["type"] == TYPE_CAPABILITY for source in sources
        ),
        "workorder_count": sum(
            source[FIELD_PAYLOAD]["type"] == TYPE_WORKORDER for source in sources
        ),
        "sources": sources,
        FIELD_PAYLOAD: payload,
        FIELD_PAYLOAD_SHA256: payload_sha256(payload),
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    sources = manifest["sources"]
    identifiers = [source[FIELD_PAYLOAD][FIELD_EXTERNAL_ID] for source in sources]
    if not identifiers:
        raise ValueError("steering manifest is empty")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("steering source IDs must be unique")
    if manifest["capability_count"] < 1 or manifest["workorder_count"] < 1:
        raise ValueError("capability and workorder scopes must both be non-empty")
    payload_items = manifest[FIELD_PAYLOAD][FIELD_ITEMS]
    if len(payload_items) != len(sources):
        raise ValueError("steering source and payload counts differ")


def _requested_fields(item: dict[str, Any]) -> tuple[str, ...]:
    return tuple(item)


def _compare_mapping(
    expected: dict[str, Any], actual: Any, path: str, mismatches: list[str]
) -> None:
    if not isinstance(actual, dict):
        mismatches.append(f"{path}: expected object")
        return
    for field, value in expected.items():
        if field not in actual:
            mismatches.append(f"{path}.{field}: missing")
            continue
        _compare_requested(value, actual[field], f"{path}.{field}", mismatches)


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError("date-time value must be a string")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("date-time value must include a timezone")
    return parsed


def _compare_datetime(
    expected: Any, actual: Any, path: str, mismatches: list[str]
) -> None:
    if expected is None or actual is None:
        if expected != actual:
            mismatches.append(f"{path}: value differs")
        return
    try:
        values_match = _parse_datetime(expected) == _parse_datetime(actual)
    except (TypeError, ValueError):
        mismatches.append(f"{path}: invalid date-time")
        return
    if not values_match:
        mismatches.append(f"{path}: value differs")


def _compare_sequence(
    expected: list[Any], actual: Any, path: str, mismatches: list[str]
) -> None:
    if not isinstance(actual, list):
        mismatches.append(f"{path}: expected array")
        return
    if len(expected) != len(actual):
        mismatches.append(f"{path}: item count differs")
        return
    for index, value in enumerate(expected):
        _compare_requested(value, actual[index], f"{path}[{index}]", mismatches)


def _compare_requested(
    expected: Any, actual: Any, path: str, mismatches: list[str]
) -> None:
    if path.rsplit(".", 1)[-1] in DATETIME_FIELDS:
        _compare_datetime(expected, actual, path, mismatches)
        return
    if isinstance(expected, dict):
        _compare_mapping(expected, actual, path, mismatches)
        return
    if isinstance(expected, list):
        _compare_sequence(expected, actual, path, mismatches)
        return
    if expected != actual:
        mismatches.append(f"{path}: value differs")


def verify_export(manifest: dict[str, Any], exported: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    remote_items = {
        item.get(FIELD_EXTERNAL_ID): item
        for item in exported.get(FIELD_ITEMS, [])
        if item.get(FIELD_SOURCE) == SOURCE
    }
    expected_items = manifest[FIELD_PAYLOAD][FIELD_ITEMS]
    if len(remote_items) != len(expected_items):
        mismatches.append("item count differs")
    for expected in expected_items:
        external_id = expected[FIELD_EXTERNAL_ID]
        actual = remote_items.get(external_id)
        if not actual:
            mismatches.append(f"{external_id}: missing")
            continue
        for field in _requested_fields(expected):
            if field not in actual:
                mismatches.append(f"{external_id}.{field}: missing")
                continue
            _compare_requested(
                expected[field],
                actual[field],
                f"{external_id}.{field}",
                mismatches,
            )
        if not CONTENT_HASH_PATTERN.fullmatch(
            str(actual.get(FIELD_CONTENT_SHA256, ""))
        ):
            mismatches.append(f"{external_id}.content_sha256: invalid")
    return mismatches


def stable_key(command_revision: str, manifest_hash: str) -> str:
    value = f"{command_revision}:{manifest_hash}"
    digest = hashlib.sha256(value.encode()).hexdigest()[:24]
    return f"apistra-steering-import-{digest}"


def _validate_jcs_value(value: Any) -> None:
    """Reject values outside the I-JSON subset used by Steering imports."""
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        if abs(value) > MAX_IJSON_INTEGER:
            raise ValueError("Steering hash integer is outside the I-JSON range")
        return
    if isinstance(value, float):
        raise TypeError("Steering imports must not contain floating-point values")
    if isinstance(value, list):
        for item in value:
            _validate_jcs_value(item)
        return
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Steering hash object keys must be strings")
        for item in value.values():
            _validate_jcs_value(item)
        return
    raise TypeError(f"Unsupported Steering hash value: {type(value).__name__}")


def _jcs_ordered(value: Any) -> Any:
    """Order object keys by UTF-16 code units as required by RFC 8785."""
    if isinstance(value, dict):
        return {
            key: _jcs_ordered(value[key])
            for key in sorted(value, key=lambda item: item.encode("utf-16-be"))
        }
    if isinstance(value, list):
        return [_jcs_ordered(item) for item in value]
    return value


def steering_payload_sha256(payload: Any) -> str:
    """Hash a Steering request using RFC 8785 for its schema-safe JSON subset."""
    _validate_jcs_value(payload)
    canonical = json.dumps(
        _jcs_ordered(payload),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def import_payloads(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Split an ordered manifest into API-sized, independently replayable writes."""
    payload = manifest[FIELD_PAYLOAD]
    items = payload[FIELD_ITEMS]
    return [
        {
            "contract_version": payload["contract_version"],
            FIELD_SOURCE: payload[FIELD_SOURCE],
            FIELD_ITEMS: items[offset : offset + MAX_IMPORT_ITEMS],
        }
        for offset in range(0, len(items), MAX_IMPORT_ITEMS)
    ]


def _validate_import_receipt(
    receipt: dict[str, Any], batch_payload: dict[str, Any]
) -> None:
    mismatches = []
    remote_hash = receipt.get(FIELD_PAYLOAD_SHA256)
    hash_contract = receipt.get(FIELD_PAYLOAD_HASH_CONTRACT)
    accepted = receipt.get("accepted_items")
    historical = receipt.get("historical_items")
    if not isinstance(remote_hash, str) or not CONTENT_HASH_PATTERN.fullmatch(
        remote_hash
    ):
        mismatches.append("receipt payload_sha256 is invalid")
    elif hash_contract == CURRENT_PAYLOAD_HASH_CONTRACT:
        if remote_hash != steering_payload_sha256(batch_payload):
            mismatches.append(
                "receipt payload_sha256 differs from the JCS request hash"
            )
    elif hash_contract == LEGACY_PAYLOAD_HASH_CONTRACT:
        if receipt.get("replayed") is not True:
            mismatches.append("legacy receipt hash is only valid for a replay")
    else:
        mismatches.append("receipt payload_hash_contract is unsupported")
    if (
        type(accepted) is not int
        or type(historical) is not int
        or accepted < 0
        or historical < 0
    ):
        mismatches.append("receipt item counts are invalid")
    elif accepted + historical != len(batch_payload[FIELD_ITEMS]):
        mismatches.append("receipt accepted/historical item total differs")
    if mismatches:
        raise ValueError("; ".join(mismatches))


def _publish_batches(
    *,
    import_url: str,
    token: str,
    manifest: dict[str, Any],
    command_revision: str,
    requester: Requester,
) -> list[dict[str, Any]]:
    completed: list[dict[str, Any]] = []
    for batch_number, batch_payload in enumerate(import_payloads(manifest), 1):
        batch_hash = steering_payload_sha256(batch_payload)
        remote_receipt: dict[str, Any] | None = None
        try:
            remote_receipt = requester(
                import_url,
                token,
                method=HTTP_POST,
                key=stable_key(command_revision, batch_hash),
                payload=batch_payload,
            )
            _validate_import_receipt(remote_receipt, batch_payload)
        except (ApiError, OSError, ValueError) as error:
            raise SteeringPublishError(
                "import",
                error,
                completed,
                batch_number=batch_number,
                failed_receipt=remote_receipt,
            ) from error
        completed.append(
            {
                "batch_number": batch_number,
                "item_count": len(batch_payload[FIELD_ITEMS]),
                "request_payload_sha256": batch_hash,
                "remote_receipt": remote_receipt,
            }
        )
    return completed


def publish_manifest(
    *,
    base_url: str,
    project_id: str,
    token: str,
    manifest: dict[str, Any],
    command_revision: str,
    requester: Requester = request_json,
) -> dict[str, Any]:
    root = f"{base_url}/api/v1/projects/{project_id}/steering"
    remote_receipts = _publish_batches(
        import_url=f"{root}/imports",
        token=token,
        manifest=manifest,
        command_revision=command_revision,
        requester=requester,
    )
    try:
        exported = requester(f"{root}/export", token)
    except (ApiError, OSError, ValueError) as error:
        raise SteeringPublishError("export", error, remote_receipts) from error
    mismatches = verify_export(manifest, exported)
    if mismatches:
        error = ValueError("steering readback mismatch: " + "; ".join(mismatches))
        raise SteeringPublishError("export_verification", error, remote_receipts)
    return {
        "verified": True,
        "project_id": project_id,
        FIELD_SOURCE: SOURCE,
        "command_revision": command_revision,
        FIELD_PAYLOAD_SHA256: manifest[FIELD_PAYLOAD_SHA256],
        "batch_count": len(remote_receipts),
        "remote_receipts": remote_receipts,
        "export_state_sha256": exported.get("state_sha256", ""),
        FIELD_ITEMS: [
            {
                FIELD_EXTERNAL_ID: item[FIELD_EXTERNAL_ID],
                "source_revision": item["source_revision"],
                FIELD_CONTENT_SHA256: item[FIELD_CONTENT_SHA256],
            }
            for item in exported[FIELD_ITEMS]
            if item.get(FIELD_SOURCE) == SOURCE
        ],
    }


def write_failure_receipt(
    path: Path,
    *,
    project_id: str,
    token: str,
    manifest_hash: str,
    command_revision: str,
    error: Exception,
) -> None:
    cause = error.cause if isinstance(error, SteeringPublishError) else error
    problem = cause.errors if isinstance(cause, ApiError) else {}
    payload = {
        "verified": False,
        "project_id": project_id,
        FIELD_SOURCE: SOURCE,
        "command_revision": command_revision,
        FIELD_PAYLOAD_SHA256: manifest_hash,
        "failure": {
            "error_type": type(cause).__name__,
            "detail": str(cause),
            "problem": problem,
        },
    }
    if isinstance(error, SteeringPublishError):
        payload["failure"]["phase"] = error.phase
        payload["failure"]["batch_number"] = error.batch_number
        payload["completed_batches"] = error.completed_batches
        payload["failed_receipt"] = error.failed_receipt
    write_json_atomic(path, redact(payload, (token,)))


def safe_failure_summary(error: Exception) -> str:
    """Expose actionable protocol metadata without response bodies or secrets."""
    cause = error.cause if isinstance(error, SteeringPublishError) else error
    parts = [type(error).__name__]
    if isinstance(error, SteeringPublishError):
        parts.append(f"phase={error.phase}")
        if error.batch_number is not None:
            parts.append(f"batch={error.batch_number}")
    if isinstance(cause, ApiError):
        parts.append(f"http={cause.status}")
        if cause.code:
            parts.append(f"code={cause.code}")
        if cause.request_id:
            parts.append(f"request_id={cause.request_id}")
    return " ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--command-revision", default="steering-contract-v3")
    args = parser.parse_args()
    manifest = build_manifest()
    write_json_atomic(args.outbox, manifest)
    if not args.apply:
        print(
            "Steering manifest validated: "
            f"{manifest['capability_count']} capabilities and "
            f"{manifest['workorder_count']} workorders."
        )
        return 0
    project_id = os.getenv("SOFTWARETEST_PROJECT_ID", "")
    token = os.getenv("SOFTWARETEST_TOKEN", "")
    if not project_id or not token:
        print("BLOCKED: SOFTWARETEST_PROJECT_ID and SOFTWARETEST_TOKEN are required")
        return 2
    base_url = os.getenv("SOFTWARETEST_BASE_URL", "https://softwaretest.it").rstrip("/")
    try:
        receipt = publish_manifest(
            base_url=base_url,
            project_id=project_id,
            token=token,
            manifest=manifest,
            command_revision=args.command_revision,
        )
        write_json_atomic(args.receipt, redact(receipt, (token,)))
        print("Softwaretest.it steering round-trip passed.")
        return 0
    except (ApiError, OSError, SteeringPublishError, ValueError) as error:
        write_failure_receipt(
            args.receipt,
            project_id=project_id,
            token=token,
            manifest_hash=manifest[FIELD_PAYLOAD_SHA256],
            command_revision=args.command_revision,
            error=error,
        )
        print(
            "Softwaretest.it steering round-trip failed safely: "
            f"{safe_failure_summary(error)}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
