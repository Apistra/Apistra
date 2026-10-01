"""Generate deterministic CAP-01 fixture descriptors without mutating product state."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
FIXTURE_REVISION = "CAP-01-FX-0.2"
FIXTURE_IDS = (
    "FX-PRC-01-FRESH",
    "FX-PRC-01-ADMIN-NO-PROJECT",
    "FX-PRC-01-ISOLATION",
)
ATLAS_ID = "11111111-1111-4111-8111-111111111111"
ORION_ID = "22222222-2222-4222-8222-222222222222"


def _base(run_id: str, fixture_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_revision": FIXTURE_REVISION,
        "fixture_id": fixture_id,
        "run_id": run_id,
        "synthetic": True,
        "target": "isolated-local-staging",
        "application_mode": "guarded-database-reset",
        "credential_references": ["env:STAGING_ADMIN_PASSWORD"],
        "cleanup": {"method": "restore-named-snapshot", "destructive_ui": False},
    }


def descriptors(run_id: str) -> dict[str, dict[str, Any]]:
    """Return the complete deterministic descriptor set for one isolated run."""
    fresh = _base(run_id, FIXTURE_IDS[0])
    fresh.update(
        {
            "administrator": None,
            "projects": [],
            "expected_state": {"bootstrap_available": True},
        }
    )

    admin = _base(run_id, FIXTURE_IDS[1])
    admin.update(
        {
            "administrator": {"username": "admin.alpha", "bootstrap_complete": True},
            "projects": [],
            "expected_state": {"bootstrap_available": False},
        }
    )

    isolation = _base(run_id, FIXTURE_IDS[2])
    isolation.update(
        {
            "administrator": {"username": "admin.alpha", "bootstrap_complete": True},
            "projects": [
                {
                    "id": ATLAS_ID,
                    "name": "Atlas Research",
                    "key": "ATLAS",
                    "authorised": True,
                },
                {
                    "id": ORION_ID,
                    "name": "Orion Restricted",
                    "key": "ORION",
                    "authorised": False,
                },
            ],
            "expected_state": {
                "bootstrap_available": False,
                "foreign_project_disclosure": False,
            },
        }
    )
    return {
        descriptor["fixture_id"]: descriptor for descriptor in (fresh, admin, isolation)
    }


def run_directory(root: Path, run_id: str) -> Path:
    if not run_id or any(
        character
        not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in run_id
    ):
        raise ValueError("run ID contains unsafe characters")
    return root.resolve() / f"cap01-{run_id}"


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _checksum(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def expected_manifest(run_id: str) -> dict[str, object]:
    fixture_set = descriptors(run_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_revision": FIXTURE_REVISION,
        "run_id": run_id,
        "synthetic": True,
        "application_mode": "guarded-database-reset",
        "fixtures": [
            {
                "id": fixture_id,
                "path": f"{fixture_id}.json",
                "sha256": _checksum(fixture_set[fixture_id]),
            }
            for fixture_id in FIXTURE_IDS
        ],
    }


def setup(root: Path, run_id: str) -> Path:
    """Write an idempotent descriptor package for a future staging application."""
    directory = run_directory(root, run_id)
    directory.mkdir(parents=True, exist_ok=True)
    for fixture_id, descriptor in descriptors(run_id).items():
        directory.joinpath(f"{fixture_id}.json").write_bytes(
            _canonical_bytes(descriptor)
        )
    directory.joinpath("manifest.json").write_bytes(
        _canonical_bytes(expected_manifest(run_id))
    )
    return directory


def verify(root: Path, run_id: str) -> bool:
    """Verify exact content and checksums; never infer staging application."""
    directory = run_directory(root, run_id)
    expected = descriptors(run_id)
    if json.loads(directory.joinpath("manifest.json").read_text()) != expected_manifest(
        run_id
    ):
        return False
    for fixture_id, descriptor in expected.items():
        path = directory / f"{fixture_id}.json"
        if not path.is_file() or path.read_bytes() != _canonical_bytes(descriptor):
            return False
    return True


def cleanup(root: Path, run_id: str) -> None:
    directory = run_directory(root, run_id)
    if directory.parent != root.resolve() or not directory.name.startswith("cap01-"):
        raise ValueError("cleanup target escaped fixture root")
    if directory.exists():
        shutil.rmtree(directory)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["setup", "verify", "reset", "cleanup"])
    parser.add_argument("--root", type=Path, default=Path("artifacts/fixtures"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    if args.action == "setup":
        print(setup(args.root, args.run_id))
    elif args.action == "verify":
        if not verify(args.root, args.run_id):
            return 1
        print(
            "CAP-01 fixture descriptors verified; database application requires guarded entrypoint."
        )
    elif args.action == "reset":
        cleanup(args.root, args.run_id)
        print(setup(args.root, args.run_id))
    else:
        cleanup(args.root, args.run_id)
        print("CAP-01 fixture descriptors removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
