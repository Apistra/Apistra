"""Manually deploy, verify, failure-test, and recover one immutable candidate."""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose/compose.staging.yml"
UTF8 = "utf-8"
FIELD_USERNAME = "username"
FIELD_KEY = "key"
FIELD_STATUS = "status"
FIELD_ID = "id"
FIELD_ITEMS = "items"
FIELD_EVENT_TYPE = "event_type"
FIELD_IMAGES = "images"
FIELD_REFERENCE = "reference"
HEADER_CONTENT_TYPE = "content-type"
HEADER_CORRELATION_ID = "x-correlation-id"
HEADER_COOKIE = "cookie"
HEADER_CSRF_TOKEN = "x-csrf-token"
JSON_MEDIA_TYPE = "application/json"
HTTP_POST = "POST"
ATLAS_KEY = "ATLAS"
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
SECRET_KEY_BYTES = 32
SECRET_KEY_ID = "local-v1"
OWNER_ONLY_MODE = 0o600
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
DEFAULT_API_PORT = 18_080
DEFAULT_WEB_PORT = 13_000
DATABASE_PASSWORD_BYTES = 32


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


def _bootstrap_administrator(web_base: str) -> tuple[str, str, dict[str, object], str]:
    username = "candidate-administrator"
    password = secrets.token_urlsafe(24)
    request = urllib.request.Request(
        f"{web_base}/api/v1/administrators:bootstrap",
        data=json.dumps({FIELD_USERNAME: username, "password": password}).encode(UTF8),
        headers={
            HEADER_CONTENT_TYPE: JSON_MEDIA_TYPE,
            HEADER_CORRELATION_ID: "staging-bootstrap",
        },
        method=HTTP_POST,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != HTTP_CREATED:
            raise RuntimeError("administrator bootstrap did not return 201")
        receipt = json.load(response)
        set_cookie = response.headers.get("set-cookie", "")
    if not all(
        attribute in set_cookie for attribute in ("HttpOnly", "SameSite=strict")
    ):
        raise RuntimeError(
            "administrator session cookie is missing required security attributes"
        )
    if "Secure" in set_cookie:
        raise RuntimeError(
            "loopback HTTP candidate issued a browser-incompatible Secure cookie"
        )
    session_cookie = set_cookie.split(";", 1)[0]
    if receipt.get("administrator", {}).get(FIELD_USERNAME) != username:
        raise RuntimeError("administrator bootstrap receipt did not match")
    return username, password, receipt, session_cookie


def _create_project(
    web_base: str, session_cookie: str, csrf_token: str
) -> dict[str, object]:
    project_request = urllib.request.Request(
        f"{web_base}/api/v1/projects",
        data=json.dumps({"name": "Atlas Research", FIELD_KEY: ATLAS_KEY}).encode(UTF8),
        headers={
            HEADER_CONTENT_TYPE: JSON_MEDIA_TYPE,
            HEADER_COOKIE: session_cookie,
            "idempotency-key": "staging-create-atlas",
            HEADER_CORRELATION_ID: "staging-project-create",
            HEADER_CSRF_TOKEN: csrf_token,
        },
        method=HTTP_POST,
    )
    with urllib.request.urlopen(project_request, timeout=5) as response:
        if response.status != HTTP_CREATED or response.headers.get("etag") != '"1"':
            raise RuntimeError("project creation did not return its initial version")
        project = json.load(response)
    if project.get(FIELD_KEY) != ATLAS_KEY or project.get(FIELD_STATUS) != "ACTIVE":
        raise RuntimeError("project creation receipt did not match")
    return project


def _verify_project_list(
    web_base: str, session_cookie: str, project_id: object
) -> None:
    listed_request = urllib.request.Request(
        f"{web_base}/api/v1/projects", headers={HEADER_COOKIE: session_cookie}
    )
    listed = json.load(urllib.request.urlopen(listed_request, timeout=3))
    if [item.get(FIELD_ID) for item in listed.get(FIELD_ITEMS, [])] != [project_id]:
        raise RuntimeError("authorised project list did not match")


def _update_and_archive_project(
    web_base: str, session_cookie: str, csrf_token: str, project_id: object
) -> None:
    update_request = urllib.request.Request(
        f"{web_base}/api/v1/projects/{project_id}",
        data=json.dumps({"name": "Atlas Platform", FIELD_KEY: "ATLAS-2"}).encode(UTF8),
        headers={
            HEADER_CONTENT_TYPE: JSON_MEDIA_TYPE,
            HEADER_COOKIE: session_cookie,
            "if-match": '"1"',
            HEADER_CSRF_TOKEN: csrf_token,
        },
        method="PATCH",
    )
    with urllib.request.urlopen(update_request, timeout=5) as response:
        updated = json.load(response)
    if updated.get("version") != 2 or updated.get(FIELD_KEY) != "ATLAS-2":
        raise RuntimeError("version-checked project update did not match")
    archive_request = urllib.request.Request(
        f"{web_base}/api/v1/projects/{project_id}:archive",
        data=b"",
        headers={
            HEADER_COOKIE: session_cookie,
            "if-match": '"2"',
            HEADER_CSRF_TOKEN: csrf_token,
        },
        method=HTTP_POST,
    )
    archived = json.load(urllib.request.urlopen(archive_request, timeout=5))
    if archived.get(FIELD_STATUS) != "ARCHIVED" or archived.get("version") != 3:
        raise RuntimeError("version-checked project archive did not match")


def _verify_audit(
    web_base: str, session_cookie: str, username: str, project_id: object
) -> None:
    audit_request = urllib.request.Request(
        f"{web_base}/api/v1/audit-events", headers={HEADER_COOKIE: session_cookie}
    )
    audit = json.load(urllib.request.urlopen(audit_request, timeout=3))
    events = audit.get(FIELD_ITEMS, [])
    event_types = {event.get(FIELD_EVENT_TYPE) for event in events}
    if not {
        "administrator.bootstrap.completed",
        "project.created",
    }.issubset(event_types):
        raise RuntimeError("authenticated audit did not contain required CAP-01 events")
    project_events = [
        event for event in events if event.get(FIELD_EVENT_TYPE) == "project.created"
    ]
    if len(project_events) != 1:
        raise RuntimeError(
            "authenticated audit did not contain exactly one project creation"
        )
    if project_events != [
        {
            FIELD_ID: project_events[0].get(FIELD_ID),
            FIELD_EVENT_TYPE: "project.created",
            "created_at": project_events[0].get("created_at"),
            "correlation_id": "staging-project-create",
            "actor": username,
            "subject_id": project_id,
            "project_id": project_id,
            "project_key": ATLAS_KEY,
        }
    ]:
        raise RuntimeError(
            "project audit attribution did not match the authenticated context"
        )


def _verify_revocation(
    web_base: str, session_cookie: str, csrf_token: str, username: str
) -> None:
    current_request = urllib.request.Request(
        f"{web_base}/api/v1/session", headers={HEADER_COOKIE: session_cookie}
    )
    current = json.load(urllib.request.urlopen(current_request, timeout=3))
    if current.get("administrator", {}).get(FIELD_USERNAME) != username:
        raise RuntimeError("issued session was not readable")
    revoke = urllib.request.Request(
        f"{web_base}/api/v1/session",
        headers={HEADER_COOKIE: session_cookie, HEADER_CSRF_TOKEN: csrf_token},
        method="DELETE",
    )
    with urllib.request.urlopen(revoke, timeout=3) as response:
        if response.status != HTTP_NO_CONTENT:
            raise RuntimeError("session revocation did not return 204")
    try:
        urllib.request.urlopen(current_request, timeout=3)
    except urllib.error.HTTPError as error:
        if error.code != HTTP_UNAUTHORIZED:
            raise
    else:
        raise RuntimeError("revoked session remained usable")


def _sign_in_after_revocation(
    web_base: str, username: str, password: str
) -> tuple[dict[str, object], str]:
    sign_in_request = urllib.request.Request(
        f"{web_base}/api/v1/sessions",
        data=json.dumps({FIELD_USERNAME: username, "password": password}).encode(UTF8),
        headers={
            HEADER_CONTENT_TYPE: JSON_MEDIA_TYPE,
            HEADER_CORRELATION_ID: "staging-sign-in-after-revoke",
        },
        method=HTTP_POST,
    )
    with urllib.request.urlopen(sign_in_request, timeout=5) as response:
        if response.status != HTTP_CREATED:
            raise RuntimeError("sign-in after revocation did not return 201")
        new_receipt = json.load(response)
        new_cookie = response.headers.get("set-cookie", "").split(";", 1)[0]
    return new_receipt, new_cookie


def _verify_revocation_audit(web_base: str, session_cookie: str) -> None:
    post_revoke_audit = json.load(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{web_base}/api/v1/audit-events",
                headers={HEADER_COOKIE: session_cookie},
            ),
            timeout=3,
        )
    )
    if "session.revoked" not in {
        event.get(FIELD_EVENT_TYPE) for event in post_revoke_audit.get(FIELD_ITEMS, [])
    }:
        raise RuntimeError("session revocation was not attributable in the audit log")


def _revoke_cleanup_session(
    web_base: str, session_cookie: str, csrf_token: object
) -> None:
    cleanup_revoke = urllib.request.Request(
        f"{web_base}/api/v1/session",
        headers={
            HEADER_COOKIE: session_cookie,
            HEADER_CSRF_TOKEN: str(csrf_token),
        },
        method="DELETE",
    )
    with urllib.request.urlopen(cleanup_revoke, timeout=3) as response:
        if response.status != HTTP_NO_CONTENT:
            raise RuntimeError("cleanup session revocation did not return 204")


def verify_identity_round_trip(web_base: str) -> None:
    """Exercise bootstrap and immediate revocation through the web/API boundary."""

    installation = get_json(f"{web_base}/api/v1/installation")
    if installation != {"bootstrap_available": True}:
        raise RuntimeError("fresh candidate did not expose the bootstrap state")
    username, password, receipt, session_cookie = _bootstrap_administrator(web_base)
    csrf_token = str(receipt["csrf_token"])
    project = _create_project(web_base, session_cookie, csrf_token)
    project_id = project.get(FIELD_ID)
    _verify_project_list(web_base, session_cookie, project_id)
    _update_and_archive_project(web_base, session_cookie, csrf_token, project_id)
    _verify_audit(web_base, session_cookie, username, project_id)
    _verify_revocation(web_base, session_cookie, csrf_token, username)
    new_receipt, new_cookie = _sign_in_after_revocation(web_base, username, password)
    _verify_revocation_audit(web_base, new_cookie)
    _revoke_cleanup_session(web_base, new_cookie, new_receipt["csrf_token"])


def apply_cap01_fixture(
    compose: list[str], env: dict[str, str], run_id: str, fixture_id: str
) -> dict[str, object]:
    """Run the packaged, guarded fixture entrypoint and parse its secret-free receipt."""

    output = run(
        [
            *compose,
            "--profile",
            "fixtures",
            "run",
            "--rm",
            "fixture",
            fixture_id,
            "--run-id",
            run_id,
            "--confirm-reset",
            fixture_id,
        ],
        env,
        capture=True,
    )
    for line in reversed(output.splitlines()):
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if receipt.get(FIELD_STATUS) == "APPLIED":
            return receipt
    raise RuntimeError("guarded CAP-01 fixture did not emit an application receipt")


def verify_fixture_isolation(web_base: str, password: str) -> None:
    """Prove the packaged Atlas/Orion fixture through the public HTTP boundary."""

    cookies = http.cookiejar.CookieJar()
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    sign_in = urllib.request.Request(
        f"{web_base}/api/v1/sessions",
        data=json.dumps({FIELD_USERNAME: "admin.alpha", "password": password}).encode(
            UTF8
        ),
        headers={
            HEADER_CONTENT_TYPE: JSON_MEDIA_TYPE,
            HEADER_CORRELATION_ID: "staging-fixture-sign-in",
        },
        method=HTTP_POST,
    )
    with browser.open(sign_in, timeout=5) as response:
        receipt = json.load(response)

    listed = json.load(browser.open(f"{web_base}/api/v1/projects", timeout=3))
    if [
        (item.get(FIELD_ID), item.get("name"), item.get(FIELD_KEY))
        for item in listed.get(FIELD_ITEMS, [])
    ] != [
        (
            "11111111-1111-4111-8111-111111111111",
            "Atlas Research",
            ATLAS_KEY,
        )
    ]:
        raise RuntimeError(
            "fixture project listing did not preserve the owner boundary"
        )

    problems: list[dict[str, object]] = []
    for project_id in (
        "22222222-2222-4222-8222-222222222222",
        "99999999-9999-4999-8999-999999999999",
    ):
        try:
            browser.open(f"{web_base}/api/v1/projects/{project_id}", timeout=3)
        except urllib.error.HTTPError as error:
            if error.code != HTTP_NOT_FOUND:
                raise
            body = error.read().decode(UTF8)
            if "Orion Restricted" in body or "ORION" in body:
                raise RuntimeError("foreign project metadata was disclosed")
            problem = json.loads(body)
            problem.pop("correlation_id", None)
            problems.append(problem)
        else:
            raise RuntimeError("foreign or unknown fixture project was readable")
    if problems[0] != problems[1]:
        raise RuntimeError("foreign and unknown project responses were distinguishable")

    revoke = urllib.request.Request(
        f"{web_base}/api/v1/session",
        headers={
            HEADER_CSRF_TOKEN: receipt["csrf_token"],
        },
        method="DELETE",
    )
    with browser.open(revoke, timeout=3) as response:
        if response.status != HTTP_NO_CONTENT:
            raise RuntimeError("fixture session revocation did not return 204")


def wait_for(url: str, expected_status: str, timeout: float = 60) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            body = get_json(url)
            if body.get(FIELD_STATUS) == expected_status:
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
    return {
        service: image["image_id"] for service, image in manifest[FIELD_IMAGES].items()
    }


def create_secret_key_ring() -> tuple[Path, Path]:
    """Create one owner-only synthetic key ring outside retained evidence."""

    directory = Path(tempfile.mkdtemp(prefix="apistra-cap02-key-ring-"))
    path = directory / "key-ring.json"
    path.write_text(
        json.dumps(
            {
                "keys": {
                    SECRET_KEY_ID: base64.urlsafe_b64encode(
                        secrets.token_bytes(SECRET_KEY_BYTES)
                    ).decode("ascii")
                }
            }
        ),
        encoding=UTF8,
    )
    path.chmod(OWNER_ONLY_MODE)
    return directory, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    parser.add_argument("--web-port", type=int, default=DEFAULT_WEB_PORT)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding=UTF8))
    commit = manifest["source_commit"]
    secret_directory, key_ring_path = create_secret_key_ring()
    env = os.environ.copy()
    env.update(
        {
            "APISTRA_COMPOSE_PROJECT": f"apistra-cap00-{args.run_id}",
            "APISTRA_API_IMAGE": manifest[FIELD_IMAGES]["api"][FIELD_REFERENCE],
            "APISTRA_WORKER_IMAGE": manifest[FIELD_IMAGES]["worker"][FIELD_REFERENCE],
            "APISTRA_WEB_IMAGE": manifest[FIELD_IMAGES]["web"][FIELD_REFERENCE],
            "APISTRA_API_PORT": str(args.api_port),
            "APISTRA_COMMIT": commit,
            "APISTRA_DB_PASSWORD": secrets.token_urlsafe(DATABASE_PASSWORD_BYTES),
            "APISTRA_WEB_PORT": str(args.web_port),
            "APISTRA_ENVIRONMENT": f"local-staging-{args.run_id}",
            "APISTRA_SECURE_COOKIES": "false",
            "APISTRA_SECRET_KEY_RING_FILE_HOST": str(key_ring_path),
            "APISTRA_SECRET_ACTIVE_KEY_ID": SECRET_KEY_ID,
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
        web_base = f"http://127.0.0.1:{args.web_port}"
        verify_identity_round_trip(web_base)
        fixture_password = secrets.token_urlsafe(24)
        env["APISTRA_FIXTURE_GATE"] = f"apply-cap01-{args.run_id}"
        env["STAGING_ADMIN_PASSWORD"] = fixture_password
        fixture_receipt = apply_cap01_fixture(
            compose, env, args.run_id, "FX-PRC-01-ISOLATION"
        )
        if fixture_receipt.get("counts") != {
            "administrators": 2,
            "projects": 2,
        }:
            raise RuntimeError("fixture application receipt counts did not match")
        verify_fixture_isolation(web_base, fixture_password)
        env.pop("STAGING_ADMIN_PASSWORD", None)
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
                    data[FIELD_REFERENCE],
                ],
                env,
                capture=True,
            )
            for service, data in manifest[FIELD_IMAGES].items()
        }
        if before != after:
            raise RuntimeError("image identity changed during deployment or recovery")
        print(
            json.dumps(
                {
                    FIELD_STATUS: "PASSED",
                    "run_id": args.run_id,
                    "commit": commit,
                    "image_ids": after,
                    "fixture_receipt": fixture_receipt,
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        if not args.keep:
            run([*compose, "down", "--volumes", "--remove-orphans"], env, check=False)
            key_ring_path.unlink(missing_ok=True)
            secret_directory.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())
