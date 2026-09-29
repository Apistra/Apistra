from __future__ import annotations

import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
