from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOFTWARETEST = ROOT / "engineering/softwaretest"
sys.path.insert(0, str(SOFTWARETEST))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


definitions = load_module(
    "definition_publisher", SOFTWARETEST / "definition_publisher.py"
)


class DefinitionPublisherTests(unittest.TestCase):
    def test_reviewed_package_is_lossless_and_role_prefixed(self) -> None:
        manifest = definitions.build_manifest()
        self.assertEqual(len(manifest["definitions"]), 6)
        self.assertEqual(
            [item["stable_id"] for item in manifest["definitions"]],
            [f"MT-PRC-01-{index:03d}" for index in range(1, 7)],
        )
        self.assertEqual(
            [len(item["payload"]["steps"]) for item in manifest["definitions"]],
            [11, 9, 6, 12, 12, 10],
        )
        for item in manifest["definitions"]:
            self.assertEqual(len(item["source_sha256"]), 64)
            self.assertEqual(len(item["payload_sha256"]), 64)
            for step in item["payload"]["steps"]:
                self.assertRegex(step["action"], r"^[^:]+: .+")
                self.assertTrue(step["expected"])

    def test_invalid_or_incomplete_case_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(1, 7):
                path = root / f"MT-PRC-01-{index:03d}.md"
                path.write_text(
                    f"# MT-PRC-01-{index:03d} — Example\n\nVersion: 1\n",
                    encoding="utf-8",
                )
            with self.assertRaises(ValueError):
                definitions.build_manifest(root)

    def test_readback_detects_field_and_order_drift(self) -> None:
        payload = definitions.build_manifest()["definitions"][0]["payload"]
        actual = {**payload, "status": "RELEASED"}
        self.assertEqual(definitions.verify_definition(payload, actual), [])
        actual["steps"] = list(reversed(actual["steps"]))
        self.assertEqual(definitions.verify_definition(payload, actual), ["steps"])

    def test_publish_creates_releases_and_reads_back_without_results(self) -> None:
        manifest = definitions.build_manifest()
        calls: list[tuple[str, str, str, str, dict | None]] = []
        documents: dict[str, dict] = {}
        sequence = 0

        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            nonlocal sequence
            calls.append((url, method, key, if_match, payload))
            if "/cycles?" in url:
                return {"results": []}
            if url.endswith("/cycles"):
                return {
                    "id": "cycle-1",
                    "name": definitions.CYCLE["name"],
                    "status": "DRAFT",
                    "build": definitions.CYCLE["build"],
                    "environment": definitions.CYCLE["environment"],
                }
            if "/testcases?" in url:
                return {"results": []}
            if url.endswith("/testcases:guided"):
                sequence += 1
                testcase_id = f"testcase-{sequence}"
                version_id = f"version-{sequence}"
                document = {
                    "id": version_id,
                    "number": 1,
                    "status": "DRAFT",
                    "title": payload["name"],
                    "description": payload["description"],
                    "preconditions": "",
                    "priority": payload["priority"],
                    "estimated_minutes": None,
                    "steps": [],
                    "revision": 1,
                    "testcase": {
                        "id": testcase_id,
                        "key": f"APISTRA-TC-{sequence:06d}",
                        "revision": 1,
                    },
                }
                documents[version_id] = document
                return document
            if method == "PATCH":
                version_id = url.rsplit("/", 1)[1]
                document = documents[version_id]
                document.update(payload)
                document["revision"] += 1
                return document
            if url.endswith(":release"):
                version_id = url.rsplit("/", 1)[1].removesuffix(":release")
                document = documents[version_id]
                document["status"] = "RELEASED"
                document["revision"] += 1
                return document
            if method == "GET" and "/versions/" in url:
                return documents[url.rsplit("/", 1)[1]]
            raise AssertionError((url, method))

        receipt = definitions.publish_manifest(
            base_url="https://softwaretest.it",
            project_id="project-1",
            token="secret",
            manifest=manifest,
            command_revision="test-v1",
            requester=fake_request,
        )
        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["execution_results_created"], 0)
        self.assertEqual(len(receipt["definitions"]), 6)
        self.assertTrue(
            all(item["status"] == "RELEASED" for item in receipt["definitions"])
        )
        self.assertFalse(
            any("executions" in call[0] or "/results" in call[0] for call in calls)
        )

    def test_released_exact_definition_is_read_only(self) -> None:
        definition = definitions.build_manifest()["definitions"][0]
        expected_payload = definition["payload"]
        document = {
            **expected_payload,
            "id": "version-1",
            "number": 1,
            "status": "RELEASED",
            "revision": 3,
            "testcase": {
                "id": "testcase-1",
                "key": "APISTRA-TC-000002",
                "revision": 4,
            },
        }
        writes: list[str] = []

        def fake_request(
            url, token, *, method="GET", key="", if_match="", payload=None
        ):
            if method != "GET":
                writes.append(url)
            if "/testcases?" in url:
                return {
                    "results": [
                        {
                            "id": "testcase-1",
                            "latest_version": {
                                "id": "version-1",
                                "title": expected_payload["title"],
                            },
                        }
                    ]
                }
            return document

        result = definitions.publish_definition(
            root="https://softwaretest.it/api/v1/projects/project-1/testcases",
            cycle_id="cycle-1",
            token="secret",
            definition=definition,
            command_revision="test-v1",
            requester=fake_request,
        )
        self.assertTrue(result["verified"])
        self.assertFalse(result["changed"])
        self.assertEqual(writes, [])


if __name__ == "__main__":
    unittest.main()
