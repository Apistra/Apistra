from __future__ import annotations

import hashlib
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
        self.assertEqual(items["CAP-01"]["approval_status"], "APPROVED")
        self.assertEqual(items["CAP-01"]["evidence_status"], "CURRENT")
        self.assertEqual(items["CAP-02"]["implementation_status"], "IN_PROGRESS")
        self.assertEqual(items["WO-CAP-00-06"]["evidence_status"], "CURRENT")
        self.assertEqual(items["WO-CAP-00-08"]["implementation_status"], "IMPLEMENTED")
        self.assertEqual(items["WO-CAP-00-08"]["approval_status"], "APPROVED")
        self.assertEqual(items["WO-CAP-00-08"]["evidence_status"], "CURRENT")
        self.assertEqual(items["WO-CAP-00-08"]["transmission_status"], "CONFIRMED")

    def test_acceptance_criteria_require_explicit_source_evidence(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        items = {
            source["payload"]["external_id"]: source["payload"]
            for source in manifest["sources"]
        }
        self.assertTrue(
            all(
                row["status"] == "PASSED" and row["due_now"]
                for row in items["CAP-00"]["criteria"]
            )
        )
        self.assertTrue(
            all(
                row["status"] == "PASSED" and row["due_now"]
                for row in items["WO-CAP-00-08"]["criteria"]
            )
        )
        self.assertTrue(
            all(
                row["status"] == "PASSED" and row["due_now"]
                for row in items["CAP-01"]["criteria"]
            )
        )
        self.assertTrue(
            all(
                row["status"] == "PASSED" and row["due_now"]
                for row in items["WO-CAP-01-05"]["criteria"]
            )
        )
        self.assertTrue(
            all(
                row["status"] == "UNKNOWN" and not row["due_now"]
                for row in items["CAP-02"]["criteria"]
            )
        )

    def test_source_revision_includes_projection_contract_revision(self) -> None:
        self.assertEqual(steering._source_revision("0.3"), 300_102)
        self.assertEqual(steering._source_revision("1.1"), 100_100_102)
        self.assertGreater(
            steering._source_revision("0.4"),
            steering._source_revision("0.3"),
        )

    def test_draft_blocker_explanation_does_not_activate_future_work(self) -> None:
        self.assertEqual(
            steering._implementation_status(
                "DRAFT; implementation blocked by prerequisite gates"
            ),
            steering.STATUS_PLANNED,
        )
        self.assertEqual(
            steering._implementation_status("BLOCKED"),
            steering.STATUS_BLOCKED,
        )

    def test_approval_mapping_keeps_item_and_later_gates_separate(self) -> None:
        self.assertEqual(
            steering._approval_status(
                "DONE",
                "REVIEWED — product-owner review remains applicable",
            ),
            steering.STATUS_APPROVED,
        )
        self.assertEqual(
            steering._approval_status(
                "DONE",
                "TECHNICAL WORKORDER REVIEW COMPLETE; "
                "CAPABILITY HUMAN ACCEPTANCE REMAINS WITH WO-CAP-01-05",
            ),
            steering.STATUS_APPROVED,
        )
        self.assertEqual(
            steering._approval_status(
                "READY",
                "ACCEPTANCE PLAN APPROVED; CAPABILITY NOT APPROVED",
            ),
            steering.STATUS_OPEN,
        )

    def test_repository_projection_has_only_source_active_items(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: OBSERVED_AT
        )
        items = [source["payload"] for source in manifest["sources"]]
        active = {
            item["external_id"]
            for item in items
            if item["implementation_status"] in {"IN_PROGRESS", "BLOCKED"}
            or (
                item["implementation_status"] == "IMPLEMENTED"
                and item["approval_status"] == "OPEN"
            )
        }
        waiting_review = {
            item["external_id"]
            for item in items
            if item["implementation_status"] == "IMPLEMENTED"
            and item["approval_status"] == "OPEN"
        }
        self.assertEqual(active, {"CAP-02"})
        self.assertEqual(waiting_review, set())

    def test_invalid_or_cross_source_criterion_evidence_fails_closed(self) -> None:
        malformed = """## Acceptance criteria

1. One criterion

## Steering criterion evidence

- CAP-01-AC-01: passed now
"""
        with self.assertRaisesRegex(ValueError, "invalid Steering criterion evidence"):
            steering._criteria(malformed, "CAP-01")

        cross_source = """## Acceptance criteria

1. One criterion

## Steering criterion evidence

- CAP-02-AC-01: status=PASSED; due_now=true; gate=review; reason=verified
"""
        with self.assertRaisesRegex(ValueError, "belongs to another source"):
            steering._criteria(cross_source, "CAP-01")

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
                    "payload_sha256": steering.steering_payload_sha256(payload),
                    "payload_hash_contract": "rfc8785-sha256",
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
                "payload_sha256": steering.steering_payload_sha256(payload),
                "payload_hash_contract": "rfc8785-sha256",
            },
            payload,
        )
        with self.assertRaisesRegex(ValueError, "item total differs"):
            steering._validate_import_receipt(
                {
                    "accepted_items": 0,
                    "historical_items": 0,
                    "payload_sha256": "a" * 64,
                    "payload_hash_contract": "rfc8785-sha256",
                },
                payload,
            )
        with self.assertRaisesRegex(ValueError, "item counts are invalid"):
            steering._validate_import_receipt(
                {
                    "accepted_items": -1,
                    "historical_items": 2,
                    "payload_sha256": "a" * 64,
                    "payload_hash_contract": "rfc8785-sha256",
                },
                payload,
            )

    def test_receipt_requires_declared_matching_jcs_hash(self) -> None:
        payload = {"source": "apistra", "items": [{"external_id": "CAP-01"}]}
        with self.assertRaisesRegex(ValueError, "differs from the JCS request hash"):
            steering._validate_import_receipt(
                {
                    "accepted_items": 1,
                    "historical_items": 0,
                    "replayed": False,
                    "payload_sha256": "a" * 64,
                    "payload_hash_contract": "rfc8785-sha256",
                },
                payload,
            )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            steering._validate_import_receipt(
                {
                    "accepted_items": 1,
                    "historical_items": 0,
                    "replayed": False,
                    "payload_sha256": steering.steering_payload_sha256(payload),
                },
                payload,
            )

    def test_legacy_receipt_hash_is_allowed_only_for_replay(self) -> None:
        payload = {"items": [{"external_id": "CAP-01"}]}
        receipt = {
            "accepted_items": 1,
            "historical_items": 0,
            "replayed": True,
            "payload_sha256": "a" * 64,
            "payload_hash_contract": "legacy-drf-normalized-sha256",
        }
        steering._validate_import_receipt(receipt, payload)
        receipt["replayed"] = False
        with self.assertRaisesRegex(ValueError, "only valid for a replay"):
            steering._validate_import_receipt(receipt, payload)

    def test_steering_hash_rejects_values_outside_schema_safe_jcs_subset(self) -> None:
        with self.assertRaisesRegex(TypeError, "floating-point"):
            steering.steering_payload_sha256({"value": 1.5})
        with self.assertRaisesRegex(ValueError, "I-JSON range"):
            steering.steering_payload_sha256({"value": steering.MAX_IJSON_INTEGER + 1})

    def test_steering_hash_orders_object_keys_as_utf16_code_units(self) -> None:
        value = {"\ue000": 1, "\U00010000": 2}
        canonical = '{"𐀀":2,"":1}'.encode()
        self.assertEqual(
            steering.steering_payload_sha256(value),
            hashlib.sha256(canonical).hexdigest(),
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
                "payload_sha256": steering.steering_payload_sha256(payload),
                "payload_hash_contract": "rfc8785-sha256",
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

    def test_export_compares_rfc3339_timestamps_as_instants(self) -> None:
        manifest = steering.build_manifest(
            observed_at_provider=lambda _path: "2026-10-02T08:00:00.000Z"
        )
        exported = {
            "items": [
                {
                    **item,
                    "source": steering.SOURCE,
                    "observed_at": item["observed_at"].replace(".000Z", "Z"),
                    "content_sha256": "c" * 64,
                }
                for item in manifest["payload"]["items"]
            ]
        }
        self.assertEqual(steering.verify_export(manifest, exported), [])

        confirmed_mismatches: list[str] = []
        steering._compare_requested(
            {"confirmed_at": "2026-10-02T08:00:00.000Z"},
            {"confirmed_at": "2026-10-02T10:00:00+02:00"},
            "CAP-00",
            confirmed_mismatches,
        )
        self.assertEqual(confirmed_mismatches, [])

    def test_export_rejects_changed_or_invalid_timestamp_instants(self) -> None:
        expected = {"observed_at": "2026-10-02T08:00:00.000Z"}
        equivalent = {"observed_at": "2026-10-02T10:00:00+02:00"}
        changed = {"observed_at": "2026-10-02T08:00:01Z"}
        invalid = {"observed_at": "2026-10-02 08:00:00"}

        equivalent_mismatches: list[str] = []
        steering._compare_requested(
            expected,
            equivalent,
            "CAP-00",
            equivalent_mismatches,
        )
        self.assertEqual(equivalent_mismatches, [])

        changed_mismatches: list[str] = []
        steering._compare_requested(
            expected,
            changed,
            "CAP-00",
            changed_mismatches,
        )
        self.assertEqual(
            changed_mismatches,
            ["CAP-00.observed_at: value differs"],
        )

        invalid_mismatches: list[str] = []
        steering._compare_requested(
            expected,
            invalid,
            "CAP-00",
            invalid_mismatches,
        )
        self.assertEqual(
            invalid_mismatches,
            ["CAP-00.observed_at: invalid date-time"],
        )

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
