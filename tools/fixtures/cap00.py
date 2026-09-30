"""Deterministic synthetic CAP-00 fixture descriptors; never creates product entities."""

from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path


def fixture(run_id: str) -> dict[str, object]:
    namespace = uuid.UUID("602640f4-4191-4c5b-8fcb-0f6244785cee")
    return {
        "schema_version": "1.0",
        "synthetic": True,
        "run_id": run_id,
        "administrator": {
            "external_id": str(uuid.uuid5(namespace, f"{run_id}:admin")),
            "email": f"admin+{run_id}@example.invalid",
        },
        "project": {
            "external_id": str(uuid.uuid5(namespace, f"{run_id}:project")),
            "name": f"CAP-00 {run_id}",
        },
        "data": {"classification": "synthetic", "records": []},
        "credential_references": ["env:APISTRA_TEST_CREDENTIAL"],
    }


def run_directory(root: Path, run_id: str) -> Path:
    if not run_id or any(
        character
        not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in run_id
    ):
        raise ValueError("run ID contains unsafe characters")
    return root.resolve() / f"cap00-{run_id}"


def setup(root: Path, run_id: str) -> Path:
    directory = run_directory(root, run_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "fixture.json").write_text(
        json.dumps(fixture(run_id), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return directory


def cleanup(root: Path, run_id: str) -> None:
    directory = run_directory(root, run_id)
    if directory.parent != root.resolve() or not directory.name.startswith("cap00-"):
        raise ValueError("cleanup target escaped fixture root")
    if directory.exists():
        shutil.rmtree(directory)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["setup", "verify", "reset", "cleanup"])
    parser.add_argument("--root", type=Path, default=Path("artifacts/fixtures"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    directory = run_directory(args.root, args.run_id)
    if args.action == "setup":
        print(setup(args.root, args.run_id))
    elif args.action == "verify":
        observed = json.loads((directory / "fixture.json").read_text(encoding="utf-8"))
        if observed != fixture(args.run_id):
            return 1
        print("Fixture verified.")
    elif args.action == "reset":
        cleanup(args.root, args.run_id)
        print(setup(args.root, args.run_id))
    else:
        cleanup(args.root, args.run_id)
        print("Fixture removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
