"""Manually deploy, verify, failure-test, and recover one immutable candidate."""

from __future__ import annotations

import argparse
import json
import os
import secrets
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


def verify_identity_round_trip(web_base: str) -> None:
    """Exercise bootstrap and immediate revocation through the web/API boundary."""

    installation = get_json(f"{web_base}/api/v1/installation")
    if installation != {"bootstrap_available": True}:
        raise RuntimeError("fresh candidate did not expose the bootstrap state")
    username = "candidate-administrator"
    password = secrets.token_urlsafe(24)
    request = urllib.request.Request(
        f"{web_base}/api/v1/administrators:bootstrap",
        data=json.dumps({"username": username, "password": password}).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-correlation-id": "staging-bootstrap",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != 201:
            raise RuntimeError("administrator bootstrap did not return 201")
        receipt = json.load(response)
        set_cookie = response.headers.get("set-cookie", "")
    if not all(
        attribute in set_cookie
        for attribute in ("HttpOnly", "Secure", "SameSite=strict")
    ):
        raise RuntimeError(
            "administrator session cookie is missing required security attributes"
        )
    session_cookie = set_cookie.split(";", 1)[0]
    if receipt.get("administrator", {}).get("username") != username:
        raise RuntimeError("administrator bootstrap receipt did not match")
    project_request = urllib.request.Request(
        f"{web_base}/api/v1/projects",
        data=json.dumps({"name": "Atlas Research", "key": "ATLAS"}).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "cookie": session_cookie,
            "idempotency-key": "staging-create-atlas",
            "x-correlation-id": "staging-project-create",
            "x-csrf-token": receipt["csrf_token"],
        },
        method="POST",
    )
    with urllib.request.urlopen(project_request, timeout=5) as response:
        if response.status != 201 or response.headers.get("etag") != '"1"':
            raise RuntimeError("project creation did not return its initial version")
        project = json.load(response)
    project_id = project.get("id")
    if project.get("key") != "ATLAS" or project.get("status") != "ACTIVE":
        raise RuntimeError("project creation receipt did not match")
    listed_request = urllib.request.Request(
        f"{web_base}/api/v1/projects", headers={"cookie": session_cookie}
    )
    listed = json.load(urllib.request.urlopen(listed_request, timeout=3))
    if [item.get("id") for item in listed.get("items", [])] != [project_id]:
        raise RuntimeError("authorised project list did not match")
    update_request = urllib.request.Request(
        f"{web_base}/api/v1/projects/{project_id}",
        data=json.dumps({"name": "Atlas Platform", "key": "ATLAS-2"}).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "cookie": session_cookie,
            "if-match": '"1"',
            "x-csrf-token": receipt["csrf_token"],
        },
        method="PATCH",
    )
    with urllib.request.urlopen(update_request, timeout=5) as response:
        updated = json.load(response)
    if updated.get("version") != 2 or updated.get("key") != "ATLAS-2":
        raise RuntimeError("version-checked project update did not match")
    archive_request = urllib.request.Request(
        f"{web_base}/api/v1/projects/{project_id}:archive",
        data=b"",
        headers={
            "cookie": session_cookie,
            "if-match": '"2"',
            "x-csrf-token": receipt["csrf_token"],
        },
        method="POST",
    )
    archived = json.load(urllib.request.urlopen(archive_request, timeout=5))
    if archived.get("status") != "ARCHIVED" or archived.get("version") != 3:
        raise RuntimeError("version-checked project archive did not match")
    audit_request = urllib.request.Request(
        f"{web_base}/api/v1/audit-events", headers={"cookie": session_cookie}
    )
    audit = json.load(urllib.request.urlopen(audit_request, timeout=3))
    events = audit.get("items", [])
    event_types = {event.get("event_type") for event in events}
    if not {
        "administrator.bootstrap.completed",
        "project.created",
    }.issubset(event_types):
        raise RuntimeError("authenticated audit did not contain required CAP-01 events")
    project_events = [
        event for event in events if event.get("event_type") == "project.created"
    ]
    if len(project_events) != 1:
        raise RuntimeError(
            "authenticated audit did not contain exactly one project creation"
        )
    if project_events != [
        {
            "id": project_events[0].get("id"),
            "event_type": "project.created",
            "created_at": project_events[0].get("created_at"),
            "correlation_id": "staging-project-create",
            "actor": username,
            "subject_id": project_id,
            "project_id": project_id,
            "project_key": "ATLAS",
        }
    ]:
        raise RuntimeError(
            "project audit attribution did not match the authenticated context"
        )
    current_request = urllib.request.Request(
        f"{web_base}/api/v1/session", headers={"cookie": session_cookie}
    )
    current = json.load(urllib.request.urlopen(current_request, timeout=3))
    if current.get("administrator", {}).get("username") != username:
        raise RuntimeError("issued session was not readable")
    revoke = urllib.request.Request(
        f"{web_base}/api/v1/session",
        headers={"cookie": session_cookie, "x-csrf-token": receipt["csrf_token"]},
        method="DELETE",
    )
    with urllib.request.urlopen(revoke, timeout=3) as response:
        if response.status != 204:
            raise RuntimeError("session revocation did not return 204")
    try:
        urllib.request.urlopen(current_request, timeout=3)
    except urllib.error.HTTPError as error:
        if error.code != 401:
            raise
    else:
        raise RuntimeError("revoked session remained usable")
    sign_in_request = urllib.request.Request(
        f"{web_base}/api/v1/sessions",
        data=json.dumps({"username": username, "password": password}).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-correlation-id": "staging-sign-in-after-revoke",
        },
        method="POST",
    )
    with urllib.request.urlopen(sign_in_request, timeout=5) as response:
        if response.status != 201:
            raise RuntimeError("sign-in after revocation did not return 201")
        new_receipt = json.load(response)
        new_cookie = response.headers.get("set-cookie", "").split(";", 1)[0]
    post_revoke_audit = json.load(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{web_base}/api/v1/audit-events", headers={"cookie": new_cookie}
            ),
            timeout=3,
        )
    )
    if "session.revoked" not in {
        event.get("event_type") for event in post_revoke_audit.get("items", [])
    }:
        raise RuntimeError("session revocation was not attributable in the audit log")
    cleanup_revoke = urllib.request.Request(
        f"{web_base}/api/v1/session",
        headers={
            "cookie": new_cookie,
            "x-csrf-token": new_receipt["csrf_token"],
        },
        method="DELETE",
    )
    with urllib.request.urlopen(cleanup_revoke, timeout=3) as response:
        if response.status != 204:
            raise RuntimeError("cleanup session revocation did not return 204")


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
            "APISTRA_COMMIT": commit,
            "APISTRA_DB_PASSWORD": secrets.token_urlsafe(32),
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
        verify_identity_round_trip(f"http://127.0.0.1:{args.web_port}")
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
