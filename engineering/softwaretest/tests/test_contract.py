from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preflight = load_module("preflight", ROOT / "engineering/softwaretest/preflight.py")
publisher = load_module("publisher", ROOT / "engineering/softwaretest/publisher.py")


class SoftwaretestContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(
            (ROOT / "engineering/softwaretest/contract.json").read_text(
                encoding="utf-8"
            )
        )

    def test_required_operations_and_scheme_pass(self) -> None:
        paths = {}
        for method, path in self.contract["operations"].values():
            paths.setdefault(path, {})[method.lower()] = {}
        document = {
            "openapi": "3.0.3",
            "info": {"title": "softwaretest.it REST API", "version": "1.0.0"},
            "paths": paths,
            "components": {"securitySchemes": {"ProjectBearer": {}}},
        }
        self.assertEqual(preflight.validate_openapi(document, self.contract), [])

    def test_ci_integration_guide_passes_and_drift_fails_closed(self) -> None:
        guide = {
            "contract": "softwaretest.it-ci-integration",
            "version": "1.1.0",
            "command_protocol": {
                "read_before_write": True,
                "revision_header": "If-Match",
                "idempotency_header": "Idempotency-Key",
            },
            "cycle_execution": {
                "planned_window_required": False,
                "start_preconditions": {
                    "cycle_status": "DRAFT",
                    "minimum_run_count": 1,
                    "current_revision_required": True,
                },
                "steps": [
                    {"operation_id": "cycle_create"},
                    {"operation_id": "cycle_item_create"},
                    {"operation_id": "cycle_start"},
                    {"operation_id": "run_start"},
                ],
                "failure_recovery": {
                    code: "documented"
                    for code in self.contract["integration_guide"][
                        "cycle_failure_codes"
                    ]
                },
            },
            "ci_reporting": {
                "required_scopes": ["ci:write", "read"],
                "required_headers": [
                    "Authorization",
                    "Content-Type",
                    "Idempotency-Key",
                ],
                "uses_if_match": False,
                "prerequisites": {
                    "project": "credential is bound to the project",
                    "cycle": "cycle_id identifies an existing cycle",
                    "automation_resource": (
                        "No pre-provisioned automation resource is required."
                    ),
                },
                "steps": [
                    {"operation_id": operation}
                    for operation in self.contract["integration_guide"][
                        "reporting_operations"
                    ]
                ],
                "failure_recovery": {"CI_REPORT_CYCLE_NOT_FOUND": "documented"},
            },
        }
        self.assertEqual(preflight.validate_integration_guide(guide, self.contract), [])
        guide["cycle_execution"]["steps"].pop()
        self.assertIn(
            "cycle execution operation order changed",
            preflight.validate_integration_guide(guide, self.contract),
        )
        guide["cycle_execution"]["steps"].append({"operation_id": "run_start"})
        guide["ci_reporting"]["uses_if_match"] = True
        self.assertIn(
            "CI reporting revision contract changed",
            preflight.validate_integration_guide(guide, self.contract),
        )

    def test_ci_reporting_guide_requires_no_automation_resource(self) -> None:
        self.assertFalse(
            self.contract["integration_guide"]["automation_resource_required"]
        )

    def test_contract_drift_fails_closed(self) -> None:
        self.assertGreater(
            len(
                preflight.validate_openapi(
                    {"openapi": "4.0.0", "info": {}, "paths": {}, "components": {}},
                    self.contract,
                )
            ),
            2,
        )

    def test_all_result_statuses_are_preserved(self) -> None:
        results = [
            {"test_id": f"CAP00-UNIT-{index:03d}", "status": status}
            for index, status in enumerate(sorted(publisher.ALLOWED_STATUSES), 1)
        ]
        bundle = {
            "candidate": {"commit": "a" * 40, "manifest_sha256": "b" * 64},
            "results": results,
        }
        _, entries, _ = publisher.build_payloads(bundle, "c" * 36)
        self.assertEqual(
            {entry["status"] for entry in entries}, publisher.ALLOWED_STATUSES
        )

    def test_unsupported_status_is_not_invented(self) -> None:
        bundle = {
            "candidate": {"commit": "a" * 40, "manifest_sha256": "b" * 64},
            "results": [{"test_id": "CAP00-UNIT-001", "status": "UNKNOWN"}],
        }
        with self.assertRaises(ValueError):
            publisher.build_payloads(bundle, "c" * 36)

    def test_idempotency_keys_are_stable_and_command_specific(self) -> None:
        first = publisher.stable_key("create", "candidate")
        self.assertEqual(first, publisher.stable_key("create", "candidate"))
        self.assertNotEqual(first, publisher.stable_key("finalize", "candidate"))

    def test_command_keys_rotate_with_revision_and_attempt(self) -> None:
        first = publisher.command_key("pipeline-1", "cycle", "cycle-1", "start", 1, 1)
        self.assertEqual(
            first,
            publisher.command_key("pipeline-1", "cycle", "cycle-1", "start", 1, 1),
        )
        self.assertNotEqual(
            first,
            publisher.command_key("pipeline-1", "cycle", "cycle-1", "start", 2, 2),
        )

    def test_problem_details_preserve_actionable_fields_without_headers(self) -> None:
        error = publisher.ApiError(
            409,
            {
                "code": "CYCLE_START_PRECONDITION_FAILED",
                "detail": "Cycle cannot start.",
                "request_id": "request-1",
                "errors": {"failed_precondition": "minimum_run_count"},
            },
        )
        self.assertEqual(error.code, "CYCLE_START_PRECONDITION_FAILED")
        self.assertEqual(error.request_id, "request-1")
        self.assertEqual(error.errors["failed_precondition"], "minimum_run_count")
        self.assertNotIn("Authorization", str(error))

    def test_redaction_is_recursive(self) -> None:
        self.assertEqual(
            publisher.redact({"nested": ["prefix-secret"]}, ("secret",)),
            {"nested": ["prefix-[REDACTED]"]},
        )

    def test_payload_hash_is_canonical(self) -> None:
        self.assertEqual(
            publisher.payload_sha256({"b": 2, "a": 1}),
            publisher.payload_sha256({"a": 1, "b": 2}),
        )

    def test_readback_compares_all_requested_fields(self) -> None:
        report = {
            "external_key": "cap00-a",
            "capability_ids": ["CAP-00"],
            "started_at": "2026-09-30T00:00:00+00:00",
        }
        entries = [{"test_id": "CAP00-UNIT-001", "status": "PASSED"}]
        document = {
            "status": "finalized",
            "manifest": {
                **report,
                "started_at": "2026-09-30T00:00:00Z",
                "server_owned": True,
            },
            "entries": [{**entries[0], "result_id": "server-owned"}],
        }
        self.assertEqual(publisher.verify_readback(report, entries, document), [])
        document["entries"][0]["status"] = "FAILED"
        self.assertEqual(
            publisher.verify_readback(report, entries, document),
            ["entries[0].status: value differs"],
        )

    def test_atomic_receipt_write_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            publisher.write_json_atomic(path, {"verified": True})
            self.assertEqual(json.loads(path.read_text()), {"verified": True})
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_failure_receipt_is_machine_readable_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            publisher.write_failure_receipt(
                path,
                project_id="project-1",
                base_url="https://softwaretest.it",
                token="secret-token",
                command_revision="v1",
                stage="report",
                error=RuntimeError("remote rejected secret-token"),
                cycle={"document": {"id": "cycle-1"}},
                request_sha256={"create": "a" * 64},
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            rendered = json.dumps(document)
            self.assertFalse(document["verified"])
            self.assertEqual(document["failure"]["stage"], "report")
            self.assertEqual(document["failure"]["error_type"], "RuntimeError")
            self.assertIn("[REDACTED]", document["failure"]["detail"])
            self.assertNotIn("secret-token", rendered)
            self.assertEqual(document["request_sha256"]["create"], "a" * 64)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_failure_receipt_retains_ci_cycle_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            error = publisher.ApiError(
                404,
                {
                    "code": "CI_REPORT_CYCLE_NOT_FOUND",
                    "detail": "Cycle not found.",
                    "request_id": "request-2",
                    "errors": {
                        "cycle_id": "cycle-1",
                        "remediation": "Use an existing project cycle.",
                    },
                },
            )
            publisher.write_failure_receipt(
                path,
                project_id="project-1",
                base_url="https://softwaretest.it",
                token="secret-token",
                command_revision="ci-guide-1.1",
                stage="report",
                error=error,
            )
            problem = json.loads(path.read_text())["failure"]["problem"]
            self.assertEqual(problem["code"], "CI_REPORT_CYCLE_NOT_FOUND")
            self.assertEqual(problem["errors"]["cycle_id"], "cycle-1")
            self.assertIn("remediation", problem["errors"])

    def test_roundtrip_collects_receipts_and_readbacks(self) -> None:
        report = {"external_key": "cap00-a"}
        entries = [{"test_id": "CAP00-UNIT-001", "status": "PASSED"}]
        final = {"finished_at": "2026-09-30T00:00:00+00:00"}
        calls = []

        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            calls.append((url, token, method, key, payload))
            if url.endswith("/ci-reports"):
                return {
                    "report_id": "report-1",
                    "receipt_id": "receipt-create",
                }
            if url.endswith("/entries"):
                return {
                    "report_id": "report-1",
                    "receipt_id": "receipt-entries",
                }
            if url.endswith("/finalize"):
                return {
                    "report_id": "report-1",
                    "receipt_id": "receipt-finalize",
                }
            if "/reporting-receipts/" in url:
                return {"id": url.rsplit("/", 1)[1], "status": "ACCEPTED"}
            return {
                "report_id": "report-1",
                "status": "FINALIZED",
                "manifest": report,
                "entries": entries,
            }

        result = publisher.execute_roundtrip(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            report=report,
            entries=entries,
            final=final,
            command_revision="workaround-v2",
            requester=fake_request,
        )
        self.assertTrue(result["verified"])
        self.assertEqual(
            set(result["server_receipts"]), {"create", "entries", "finalize"}
        )
        self.assertEqual(
            set(result["receipt_readbacks"]), {"create", "entries", "finalize"}
        )
        self.assertEqual(len(calls), 7)
        self.assertTrue(calls[0][3].startswith("apistra-cap00-create-"))

    def test_cycle_resolution_reuses_matching_cycle(self) -> None:
        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            if "/runs?" in url:
                return {
                    "results": [
                        {
                            "id": "run-1",
                            "cycle_id": "cycle-1",
                            "status": "IN_PROGRESS",
                            "revision": 2,
                        }
                    ]
                }
            return {
                "results": [
                    {
                        "id": "cycle-1",
                        "name": "Apistra CAP-00 Reporting",
                        "status": "ACTIVE",
                        "revision": 2,
                        "run_count": 1,
                    }
                ]
            }

        cycle, created, run = publisher.ensure_cycle(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            requester=fake_request,
        )
        self.assertEqual(cycle["id"], "cycle-1")
        self.assertFalse(created)
        self.assertEqual(run["status"], "IN_PROGRESS")

    def test_cycle_resolution_creates_with_idempotency_key(self) -> None:
        calls = []
        cycle_created = False
        item_planned = False

        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            nonlocal cycle_created, item_planned
            calls.append((url, method, key, if_match, payload))
            if method == "GET":
                if "/runs?" in url:
                    return {
                        "results": [
                            {
                                "id": "run-1",
                                "cycle_id": "cycle-1",
                                "status": "NOT_STARTED",
                                "revision": 1,
                            }
                        ]
                    }
                if item_planned:
                    return {
                        "results": [
                            {
                                "id": "cycle-1",
                                "name": "Apistra CAP-00 Reporting",
                                "status": "DRAFT",
                                "revision": 2,
                                "run_count": 1,
                            }
                        ]
                    }
                return {"results": []}
            if url.endswith("/runs/run-1:start"):
                return {
                    "id": "run-1",
                    "cycle_id": "cycle-1",
                    "status": "IN_PROGRESS",
                    "revision": 2,
                }
            if url.endswith("/cycles/cycle-1:start"):
                return {
                    "id": "cycle-1",
                    "name": "Apistra CAP-00 Reporting",
                    "status": "ACTIVE",
                    "revision": 2,
                }
            if url.endswith("/items"):
                item_planned = True
                return {"id": "run-1", "status": "PLANNED"}
            cycle_created = True
            return {
                "id": "cycle-1",
                "name": payload["name"],
                "status": "DRAFT",
                "revision": 1,
                "run_count": 0,
            }

        cycle, created, run = publisher.ensure_cycle(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            anchor_version_id="version-1",
            pipeline_run_id="pipeline-1",
            requester=fake_request,
        )
        self.assertEqual(cycle["id"], "cycle-1")
        self.assertTrue(created)
        self.assertTrue(cycle_created)
        self.assertEqual(run["status"], "IN_PROGRESS")
        cycle_create = next(
            call for call in calls if call[0].endswith("/cycles") and call[1] == "POST"
        )
        item_create = next(call for call in calls if call[0].endswith("/items"))
        cycle_start = next(
            call for call in calls if call[0].endswith("/cycles/cycle-1:start")
        )
        run_start = next(
            call for call in calls if call[0].endswith("/runs/run-1:start")
        )
        self.assertTrue(cycle_create[2].startswith("apistra-cap00-cycle-create-"))
        self.assertEqual(item_create[3], '"1"')
        self.assertEqual(cycle_start[3], '"2"')
        self.assertEqual(run_start[3], '"1"')

    def test_run_start_refetches_and_rotates_key_on_revision_conflict(self) -> None:
        calls = []
        list_count = 0

        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            nonlocal list_count
            calls.append((url, method, key, if_match, payload))
            if method == "GET":
                list_count += 1
                return {
                    "results": [
                        {
                            "id": "run-1",
                            "cycle_id": "cycle-1",
                            "status": "NOT_STARTED",
                            "revision": list_count,
                        }
                    ]
                }
            if len([call for call in calls if call[1] == "POST"]) == 1:
                raise publisher.ApiError(
                    409,
                    {
                        "code": "REVISION_CONFLICT",
                        "detail": "Revision changed.",
                        "request_id": "request-1",
                        "errors": {"current_etag": '"2"'},
                    },
                )
            return {
                "id": "run-1",
                "cycle_id": "cycle-1",
                "status": "IN_PROGRESS",
                "revision": 3,
            }

        run = publisher._start_cycle_run(
            base_url="https://softwaretest.it",
            project_id="project-1",
            cycle_id="cycle-1",
            token="secret",
            pipeline_run_id="pipeline-1",
            requester=fake_request,
        )
        posts = [call for call in calls if call[1] == "POST"]
        self.assertEqual(run["status"], "IN_PROGRESS")
        self.assertEqual([call[3] for call in posts], ['"1"', '"2"'])
        self.assertNotEqual(posts[0][2], posts[1][2])


if __name__ == "__main__":
    unittest.main()
