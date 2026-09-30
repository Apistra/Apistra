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
        paths = {
            path: {method.lower(): {}}
            for method, path in self.contract["operations"].values()
        }
        document = {
            "openapi": "3.0.3",
            "info": {"title": "softwaretest.it REST API", "version": "1.0.0"},
            "paths": paths,
            "components": {"securitySchemes": {"ProjectBearer": {}}},
        }
        self.assertEqual(preflight.validate_openapi(document, self.contract), [])

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
            return {
                "results": [
                    {
                        "id": "cycle-1",
                        "name": "Apistra CAP-00 Reporting",
                        "status": "ACTIVE",
                    }
                ]
            }

        cycle, created = publisher.ensure_cycle(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            requester=fake_request,
        )
        self.assertEqual(cycle["id"], "cycle-1")
        self.assertFalse(created)

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
            if url.endswith(":start"):
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

        cycle, created = publisher.ensure_cycle(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            anchor_version_id="version-1",
            requester=fake_request,
        )
        self.assertEqual(cycle["id"], "cycle-1")
        self.assertTrue(created)
        self.assertEqual(calls[1][1], "POST")
        self.assertTrue(calls[1][2].startswith("apistra-cap00-cycle-"))
        self.assertTrue(cycle_created)
        self.assertTrue(calls[2][0].endswith("cycle-1/items"))
        self.assertEqual(calls[2][3], '"1"')
        self.assertTrue(calls[4][0].endswith("cycle-1:start"))
        self.assertEqual(calls[4][3], '"2"')


if __name__ == "__main__":
    unittest.main()
