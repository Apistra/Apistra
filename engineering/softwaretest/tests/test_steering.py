from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOFTWARETEST = ROOT / "engineering/softwaretest"
sys.path.insert(0, str(SOFTWARETEST))
OBSERVED_AT = "2026-10-02T08:00:00Z"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


steering = load_module("steering_publisher", SOFTWARETEST / "steering_publisher.py")


class SteeringPublisherTests(unittest.TestCase):
    def test_complete_repository_manifest_is_lossless_and_unique(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        self.assertEqual(manifest["capability_count"], 19)
        self.assertEqual(manifest["workorder_count"], 141)
        self.assertEqual(len(manifest["sources"]), 160)
        identifiers = [item["payload"]["external_id"] for item in manifest["sources"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertIn("CAP-00", identifiers)
        self.assertIn("WO-CAP-00-08", identifiers)
        for source in manifest["sources"]:
            self.assertEqual(len(source["source_sha256"]), 64)
            self.assertEqual(len(source["content_sha256"]), 64)

    def test_statuses_come_from_explicit_source_state(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        items = {
            source["payload"]["external_id"]: source["payload"]
            for source in manifest["sources"]
        }
        self.assertEqual(items["CAP-00"]["implementation_status"], "IMPLEMENTED")
        self.assertEqual(items["CAP-01"]["implementation_status"], "IMPLEMENTED")
        self.assertEqual(items["CAP-01"]["approval_status"], "OPEN")
        self.assertEqual(items["CAP-01"]["evidence_status"], "MISSING")
        self.assertEqual(items["WO-CAP-00-06"]["evidence_status"], "CURRENT")
        self.assertEqual(items["WO-CAP-00-08"]["implementation_status"], "BLOCKED")
        self.assertEqual(items["WO-CAP-00-08"]["approval_status"], "OPEN")
        self.assertEqual(items["WO-CAP-00-08"]["evidence_status"], "MISSING")
        self.assertEqual(items["WO-CAP-00-08"]["transmission_status"], "PENDING")

    def test_evidence_mapping_uses_the_steering_domain_enum(self) -> None:
        examples = {
            "NOT EXECUTED": "MISSING",
            "LOCAL TESTS PASSED; NOT EXECUTED": "PARTIAL",
            "VERIFIED — trusted run": "CURRENT",
            "LOCAL AND HOSTED OWNED MATRIX VERIFIED": "CURRENT",
            "FAILED — receipt mismatch": "FAILED",
            "STALE — candidate changed": "STALE",
            "UNCLASSIFIED SOURCE TEXT": "UNKNOWN",
        }
        for source, expected in examples.items():
            with self.subTest(source=source):
                self.assertEqual(steering._evidence_status(source), expected)

        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        statuses = {item["payload"]["evidence_status"] for item in manifest["sources"]}
        self.assertLessEqual(statuses, steering.STEERING_EVIDENCE_STATUSES)

    def test_invalid_status_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported implementation status"):
            steering._implementation_status("MAYBE")

    def test_final_acceptance_ready_keeps_approval_open(self) -> None:
        source_status = "FINAL ACCEPTANCE READY; NOT ACCEPTED"
        self.assertEqual(
            steering._implementation_status(source_status),
            steering.STATUS_IMPLEMENTED,
        )
        self.assertEqual(
            steering._approval_status(source_status, ""),
            steering.STATUS_OPEN,
        )

    def test_publish_uses_bounded_imports_and_full_export_readback(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        calls = []

        def fake_request(url, token, *, method="GET", key="", payload=None, **_kwargs):
            calls.append((url, token, method, key, payload))
            if method == "POST":
                return {
                    "receipt_id": "receipt-1",
                    "accepted_items": len(payload["items"]),
                    "historical_items": 0,
                    "replayed": False,
                    "payload_sha256": steering.payload_sha256(payload),
                }
            return {
                "contract_version": "1.0",
                "project_id": "project-1",
                "generated_at": OBSERVED_AT,
                "state_sha256": "a" * 64,
                "items": [
                    {
                        **item,
                        "id": f"remote-{index}",
                        "source": steering.SOURCE,
                        "content_sha256": "b" * 64,
                    }
                    for index, item in enumerate(manifest["payload"]["items"], 1)
                ],
            }

        receipt = steering.publish_manifest(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            manifest=manifest,
            command_revision="test-v1",
            requester=fake_request,
        )
        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["batch_count"], 2)
        self.assertEqual(len(calls), 3)
        imports = [call for call in calls if call[2] == "POST"]
        self.assertEqual([len(call[4]["items"]) for call in imports], [100, 60])
        self.assertEqual(len({call[3] for call in imports}), 2)
        self.assertTrue(
            all(call[3].startswith("apistra-steering-import-") for call in imports)
        )
        imported_ids = [
            item["external_id"] for call in imports for item in call[4]["items"]
        ]
        expected_ids = [item["external_id"] for item in manifest["payload"]["items"]]
        self.assertEqual(imported_ids, expected_ids)
        self.assertTrue(calls[2][0].endswith("/steering/export"))

    def test_receipt_accepts_current_and_historical_item_total(self) -> None:
        payload = {"items": [{"external_id": "CAP-01"}]}
        steering._validate_import_receipt(
            {
                "accepted_items": 0,
                "historical_items": 1,
                "payload_sha256": "a" * 64,
            },
            payload,
        )
        with self.assertRaisesRegex(ValueError, "item total differs"):
            steering._validate_import_receipt(
                {
                    "accepted_items": 0,
                    "historical_items": 0,
                    "payload_sha256": "a" * 64,
                },
                payload,
            )
        with self.assertRaisesRegex(ValueError, "item counts are invalid"):
            steering._validate_import_receipt(
                {
                    "accepted_items": -1,
                    "historical_items": 2,
                    "payload_sha256": "a" * 64,
                },
                payload,
            )

    def test_second_batch_failure_retains_completed_batch_evidence(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        post_count = 0

        def failing_request(_url, _token, *, method="GET", payload=None, **_kwargs):
            nonlocal post_count
            if method != "POST":
                self.fail("export must not run after a failed import")
            post_count += 1
            if post_count == 2:
                raise OSError("second batch rejected")
            return {
                "accepted_items": len(payload["items"]),
                "historical_items": 0,
                "payload_sha256": steering.payload_sha256(payload),
            }

        with self.assertRaises(steering.SteeringPublishError) as raised:
            steering.publish_manifest(
                base_url="https://softwaretest.it",
                project_id="project-1",
                token="secret",
                manifest=manifest,
                command_revision="test-v2",
                requester=failing_request,
            )
        self.assertEqual(raised.exception.phase, "import")
        self.assertEqual(raised.exception.batch_number, 2)
        self.assertEqual(len(raised.exception.completed_batches), 1)

    def test_export_drift_fails_the_roundtrip(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        expected = manifest["payload"]["items"][0]
        exported = {
            "items": [
                {
                    **expected,
                    "source": steering.SOURCE,
                    "title": "Changed remotely",
                    "content_sha256": "c" * 64,
                }
            ]
        }
        mismatches = steering.verify_export(manifest, exported)
        self.assertIn("item count differs", mismatches)
        self.assertIn(f"{expected['external_id']}.title: value differs", mismatches)

    def test_failure_receipt_is_redacted_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            steering.write_failure_receipt(
                path,
                project_id="project-1",
                token="private-token",
                manifest_hash="a" * 64,
                command_revision="test-v1",
                error=RuntimeError("rejected private-token"),
            )
            receipt = json.loads(path.read_text(encoding="utf-8"))
            rendered = json.dumps(receipt)
            self.assertFalse(receipt["verified"])
            self.assertIn("[REDACTED]", rendered)
            self.assertNotIn("private-token", rendered)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_failed_remote_receipt_is_retained_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            error = steering.SteeringPublishError(
                "import",
                ValueError("receipt mismatch"),
                [],
                batch_number=1,
                failed_receipt={
                    "payload_sha256": "a" * 64,
                    "diagnostic": "private-token",
                },
            )
            steering.write_failure_receipt(
                path,
                project_id="project-1",
                token="private-token",
                manifest_hash="b" * 64,
                command_revision="test-v3",
                error=error,
            )
            receipt = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["failed_receipt"]["payload_sha256"], "a" * 64)
            self.assertEqual(receipt["failed_receipt"]["diagnostic"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
