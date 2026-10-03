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
        self.assertEqual(items["WO-CAP-00-08"]["implementation_status"], "BLOCKED")
        self.assertEqual(items["WO-CAP-00-08"]["approval_status"], "OPEN")
        self.assertEqual(items["WO-CAP-00-08"]["transmission_status"], "PENDING")

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

    def test_publish_uses_one_idempotent_import_and_full_export_readback(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        calls = []

        def fake_request(url, token, *, method="GET", key="", payload=None, **_kwargs):
            calls.append((url, token, method, key, payload))
            if method == "POST":
                return {
                    "receipt_id": "receipt-1",
                    "accepted_items": len(manifest["payload"]["items"]),
                    "historical_items": 0,
                    "replayed": False,
                    "payload_sha256": manifest["payload_sha256"],
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
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][2], "POST")
        self.assertTrue(calls[0][3].startswith("apistra-steering-import-"))
        self.assertTrue(calls[1][0].endswith("/steering/export"))

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


if __name__ == "__main__":
    unittest.main()
