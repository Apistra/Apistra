"""Generate deterministic CAP-02 descriptors without mutating product state."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
FIXTURE_REVISION = "CAP-02-FX-0.1"
TARGET = "isolated-local-staging"
APPLICATION_MODE = "future-guarded-cap02-application"
FIXTURE_IDS = (
    "FX-PRC-01-CAP02-CATALOG",
    "FX-PRC-01-CAP02-ENDPOINTS",
    "FX-PRC-01-CAP02-POLICIES",
    "FX-PRC-01-CAP02-CONFLICT",
    "FX-PRC-01-CAP02-UI",
)
ATLAS_ID = "11111111-1111-4111-8111-111111111111"
ORION_ID = "22222222-2222-4222-8222-222222222222"
PRIMARY_SECRET_ID = "33333333-3333-4333-8333-333333333333"
FOREIGN_SECRET_ID = "44444444-4444-4444-8444-444444444444"
PRIMARY_ENDPOINT_ID = "55555555-5555-4555-8555-555555555555"
FALLBACK_ENDPOINT_ID = "66666666-6666-4666-8666-666666666666"
KEY_ID = "id"
KEY_NAME = "name"
KEY_VERSION = "version"


def _base(run_id: str, fixture_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_revision": FIXTURE_REVISION,
        "fixture_id": fixture_id,
        "run_id": run_id,
        "synthetic": True,
        "target": TARGET,
        "application_mode": APPLICATION_MODE,
        "administrator": {"username": "admin.alpha", "project_id": ATLAS_ID},
        "credential_references": [
            "env:STAGING_ADMIN_PASSWORD",
            "env:CAP02_TEST_SECRET_PRIMARY",
            "env:CAP02_TEST_SECRET_ROTATED",
        ],
        "cleanup": {"method": "restore-named-snapshot", "destructive_ui": False},
    }


def _catalog(run_id: str) -> dict[str, Any]:
    value = _base(run_id, FIXTURE_IDS[0])
    value.update(
        {
            "projects": [
                {KEY_ID: ATLAS_ID, KEY_NAME: "Atlas Research", "authorised": True},
                {KEY_ID: ORION_ID, KEY_NAME: "Orion Restricted", "authorised": False},
            ],
            "secrets": [
                {
                    KEY_ID: PRIMARY_SECRET_ID,
                    KEY_NAME: "provider-primary",
                    "project_id": ATLAS_ID,
                    "value_reference": "env:CAP02_TEST_SECRET_PRIMARY",
                    "status": "ACTIVE",
                },
                {
                    KEY_ID: FOREIGN_SECRET_ID,
                    KEY_NAME: "foreign-provider",
                    "project_id": ORION_ID,
                    "value_reference": "unavailable-to-atlas",
                    "status": "ACTIVE",
                },
            ],
            "endpoints": [
                {
                    KEY_ID: PRIMARY_ENDPOINT_ID,
                    KEY_NAME: "local-llm",
                    "protocol": "OpenAI-compatible",
                    "purpose": "Generative",
                    "base_url": "http://127.0.0.1:18080/v1",
                    "model": "synthetic-chat",
                    "secret_id": PRIMARY_SECRET_ID,
                    "network_profile": "Local",
                },
                {
                    KEY_ID: FALLBACK_ENDPOINT_ID,
                    KEY_NAME: "fallback-llm",
                    "protocol": "OpenAI-compatible",
                    "purpose": "Generative",
                    "base_url": "http://127.0.0.1:18081/v1",
                    "model": "synthetic-fallback",
                    "secret_id": PRIMARY_SECRET_ID,
                    "network_profile": "Local",
                },
            ],
            "agent_draft": {
                KEY_NAME: "Research Analyst",
                "instructions": "Summarise cited research evidence.",
                "primary_endpoint_id": PRIMARY_ENDPOINT_ID,
                "fallback_endpoint_id": FALLBACK_ENDPOINT_ID,
                "tool_set": "research-readonly@2",
                "limits_policy": "interactive-default@4",
            },
        }
    )
    return value


def descriptors(run_id: str) -> dict[str, dict[str, Any]]:
    """Return the complete deterministic CAP-02 descriptor set."""
    catalog = _catalog(run_id)

    endpoints = _base(run_id, FIXTURE_IDS[1])
    endpoints.update(
        {
            "endpoint": catalog["endpoints"][0],
            "probe_profiles": {
                "verified": "http://127.0.0.1:18080/v1",
                "redirect": "http://127.0.0.1:18082/redirect",
                "metadata": "http://169.254.169.254/latest/meta-data",
                "timeout": "http://127.0.0.1:18083/timeout",
            },
            "expected_outcomes": [
                "Connection verified",
                "Destination blocked",
                "Timed out",
            ],
        }
    )

    policies = _base(run_id, FIXTURE_IDS[2])
    policies.update(
        {
            "tools": [
                {KEY_NAME: "research-readonly", KEY_VERSION: 2, "effect": "READ"},
                {KEY_NAME: "document-write", KEY_VERSION: 1, "effect": "WRITE"},
                {
                    KEY_NAME: "connector-admin",
                    KEY_VERSION: 1,
                    "effect": "ADMINISTRATIVE",
                },
            ],
            "policy": {
                KEY_NAME: "interactive-default",
                KEY_VERSION: 4,
                "maximum_duration_seconds": 300,
                "maximum_calls": 10,
                "maximum_tokens": 20000,
                "maximum_cost": {"amount": "1.50", "currency": "EUR"},
                "maximum_concurrency": 2,
                "rate_limit": {"requests": 30, "period_seconds": 60},
            },
            "boundary_samples": {"below": 9, "at": 10, "above": 11},
        }
    )

    conflict = _base(run_id, FIXTURE_IDS[3])
    conflict.update(
        {
            "policy": policies["policy"],
            "opened_revision": 4,
            "current_revision": 5,
            "unsaved_valid_input": {"maximum_calls": 12},
            "expected_message": (
                "This draft changed elsewhere. Reload the latest version before saving."
            ),
        }
    )

    ui = _base(run_id, FIXTURE_IDS[4])
    ui.update(
        {
            "viewports": [
                {KEY_NAME: "desktop", "width": 1440, "height": 900},
                {KEY_NAME: "mobile", "width": 390, "height": 844},
                {KEY_NAME: "zoom-200", "width": 640, "zoom_percent": 200},
            ],
            "routes": [
                f"/projects/{ATLAS_ID}/secrets",
                f"/projects/{ATLAS_ID}/endpoints",
                f"/projects/{ATLAS_ID}/agents",
                f"/projects/{ATLAS_ID}/tools",
                f"/projects/{ATLAS_ID}/policies/limits",
            ],
            "expected_navigation": [
                "Secrets",
                "Model Endpoints",
                "Agents",
                "Tools",
                "Limits & Policies",
            ],
        }
    )
    return {
        descriptor["fixture_id"]: descriptor
        for descriptor in (catalog, endpoints, policies, conflict, ui)
    }


def run_directory(root: Path, run_id: str) -> Path:
    if not run_id or any(
        not character.isalnum() and character not in "-_" for character in run_id
    ):
        raise ValueError("run ID contains unsafe characters")
    return root.resolve() / f"cap02-{run_id}"


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
        "application_mode": APPLICATION_MODE,
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
    """Write an idempotent descriptor package for later guarded application."""
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
    """Verify exact descriptor content; never infer staging application."""
    directory = run_directory(root, run_id)
    expected = descriptors(run_id)
    if json.loads(directory.joinpath("manifest.json").read_text()) != expected_manifest(
        run_id
    ):
        return False
    return all(
        directory.joinpath(f"{fixture_id}.json").is_file()
        and directory.joinpath(f"{fixture_id}.json").read_bytes()
        == _canonical_bytes(descriptor)
        for fixture_id, descriptor in expected.items()
    )


def cleanup(root: Path, run_id: str) -> None:
    directory = run_directory(root, run_id)
    if directory.parent != root.resolve() or not directory.name.startswith("cap02-"):
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
            "CAP-02 fixture descriptors verified; product application is not implied."
        )
    elif args.action == "reset":
        cleanup(args.root, args.run_id)
        print(setup(args.root, args.run_id))
    else:
        cleanup(args.root, args.run_id)
        print("CAP-02 fixture descriptors removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
