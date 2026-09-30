"""Manually deploy, verify, failure-test, and recover one immutable candidate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose/compose.staging.yml"


def run(
    command: list[str], env: dict[str, str], check: bool = True, capture: bool = False
) -> str:
    result = subprocess.run(
        command, cwd=ROOT, env=env, check=check, text=True, capture_output=capture
    )
    return result.stdout.strip() if capture else ""


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.load(response)


def wait_for(url: str, expected_status: str, timeout: float = 60) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            body = get_json(url)
            if body.get("status") == expected_status:
                return body
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}")


def wait_for_container_health(
    container: str, expected: str, env: dict[str, str], timeout: float = 60
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        observed = run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
            env,
            capture=True,
        )
        if observed == expected:
            return
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {container} to become {expected}")


def image_ids(manifest: dict[str, object]) -> dict[str, str]:
    return {service: image["image_id"] for service, image in manifest["images"].items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--api-port", type=int, default=18080)
    parser.add_argument("--web-port", type=int, default=13000)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    commit = manifest["source_commit"]
    env = os.environ.copy()
    env.update(
        {
            "APISTRA_COMPOSE_PROJECT": f"apistra-cap00-{args.run_id}",
            "APISTRA_API_IMAGE": manifest["images"]["api"]["reference"],
            "APISTRA_WORKER_IMAGE": manifest["images"]["worker"]["reference"],
            "APISTRA_WEB_IMAGE": manifest["images"]["web"]["reference"],
            "APISTRA_API_PORT": str(args.api_port),
            "APISTRA_WEB_PORT": str(args.web_port),
            "APISTRA_ENVIRONMENT": f"local-staging-{args.run_id}",
        }
    )
    compose = ["docker", "compose", "--file", str(COMPOSE)]
    before = image_ids(manifest)
    try:
        run([*compose, "up", "--detach", "--wait"], env)
        api = wait_for(f"http://127.0.0.1:{args.api_port}/health/ready", "ready")
        web = wait_for(f"http://127.0.0.1:{args.web_port}/api/health", "ready")
        if (
            api["deployment"]["commit"] != commit
            or web["deployment"]["commit"] != commit
        ):
            raise RuntimeError("deployment marker does not match candidate commit")
        env["APISTRA_WORKER_FORCE_NOT_READY"] = "true"
        run([*compose, "up", "--detach", "--force-recreate", "worker"], env)
        container = f"{env['APISTRA_COMPOSE_PROJECT']}-worker-1"
        wait_for_container_health(container, "unhealthy", env)
        env["APISTRA_WORKER_FORCE_NOT_READY"] = "false"
        run([*compose, "up", "--detach", "--force-recreate", "--wait", "worker"], env)
        after = {
            service: run(
                [
                    "docker",
                    "image",
                    "inspect",
                    "--format",
                    "{{.Id}}",
                    data["reference"],
                ],
                env,
                capture=True,
            )
            for service, data in manifest["images"].items()
        }
        if before != after:
            raise RuntimeError("image identity changed during deployment or recovery")
        print(
            json.dumps(
                {
                    "status": "PASSED",
                    "run_id": args.run_id,
                    "commit": commit,
                    "image_ids": after,
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        if not args.keep:
            run([*compose, "down", "--volumes", "--remove-orphans"], env, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
