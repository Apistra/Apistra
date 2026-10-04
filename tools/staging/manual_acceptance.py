"""Prepare and control a local CAP-01 manual acceptance session."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

from tools.fixtures.cap_01.generator import descriptors as fixture_descriptors
from tools.staging.verify_candidate import (
    COMPOSE,
    DATABASE_PASSWORD_BYTES,
    DEFAULT_API_PORT,
    DEFAULT_WEB_PORT,
    FIELD_IMAGES,
    FIELD_REFERENCE,
    SECRET_KEY_BYTES,
    SECRET_KEY_ID,
    apply_cap01_fixture,
    run,
    wait_for,
    write_container_secret_json,
)

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_ROOT = ROOT / "artifacts/acceptance/CAP-01"
SESSION_FILE = "session.json"
SECRET_FILE = "runtime-secrets.json"
TEST_DATA_FILE = "manual-test-data.json"
PASSWORD_FILE = "staging-admin-password.txt"
KEY_RING_FILE = "secret-key-ring.json"
UTF8 = "utf-8"
RUNNING = "RUNNING"
STOPPED = "STOPPED"
FIELD_STATUS = "status"
FIELD_RUN_ID = "run_id"
FIELD_CANDIDATE_COMMIT = "candidate_commit"
FIELD_FIXTURE = "fixture"
FIELD_ADMINISTRATOR = "administrator"
FIELD_ADMINISTRATOR_PASSWORD = "administrator_password"
FIELD_ADMINISTRATOR_USERNAME = "administrator_username"
FIELD_BOOTSTRAP_URL = "bootstrap_url"
FIELD_PASSWORD = "password"
FIELD_SIGN_IN_URL = "sign_in_url"
FIELD_USERNAME = "username"
FIELD_URLS = "urls"
ARG_RUN_ID = "--run-id"
OWNER_ONLY_MODE = 0o600
OWNER_DIRECTORY_MODE = 0o700
FIXTURE_FRESH = "FX-PRC-01-FRESH"
FIXTURE_ADMIN_NO_PROJECT = "FX-PRC-01-ADMIN-NO-PROJECT"
FIXTURE_ISOLATION = "FX-PRC-01-ISOLATION"
FIXTURES = (
    FIXTURE_FRESH,
    FIXTURE_ADMIN_NO_PROJECT,
    FIXTURE_ISOLATION,
)
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
UNKNOWN_PROJECT_ID = "99999999-9999-4999-8999-999999999999"
URL_AUDIT = "audit"
URL_SIGN_IN = "sign_in"


class ManualAcceptanceError(RuntimeError):
    """Report an expected operator error without exposing a traceback."""


def session_directory(run_id: str) -> Path:
    """Resolve a bounded evidence directory for a validated run identifier."""

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            "run ID must contain only lower-case letters, digits, or hyphens"
        )
    return ACCEPTANCE_ROOT / run_id


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding=UTF8))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding=UTF8
    )
    temporary.replace(path)


def _write_private_json(path: Path, payload: dict[str, object]) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        OWNER_ONLY_MODE,
    )
    with os.fdopen(descriptor, "w", encoding=UTF8) as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _compose_command() -> list[str]:
    return ["docker", "compose", "--file", str(COMPOSE)]


def _environment(
    state: dict[str, object], private: dict[str, object]
) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "APISTRA_COMPOSE_PROJECT": str(state["compose_project"]),
            "APISTRA_API_IMAGE": str(state["api_image"]),
            "APISTRA_WORKER_IMAGE": str(state["worker_image"]),
            "APISTRA_WEB_IMAGE": str(state["web_image"]),
            "APISTRA_API_PORT": str(state["api_port"]),
            "APISTRA_COMMIT": str(state[FIELD_CANDIDATE_COMMIT]),
            "APISTRA_DB_PASSWORD": str(private["database_password"]),
            "APISTRA_WEB_PORT": str(state["web_port"]),
            "APISTRA_ENVIRONMENT": str(state["environment"]),
            "APISTRA_SECURE_COOKIES": "false",
            "APISTRA_FIXTURE_GATE": f"apply-cap01-{state[FIELD_RUN_ID]}",
            "APISTRA_SECRET_KEY_RING_FILE_HOST": str(
                session_directory(str(state[FIELD_RUN_ID])) / KEY_RING_FILE
            ),
            "APISTRA_SECRET_ACTIVE_KEY_ID": SECRET_KEY_ID,
        }
    )
    return env


def _session_urls(web_port: int) -> dict[str, str]:
    base = f"http://127.0.0.1:{web_port}"
    return {
        FIELD_SIGN_IN_URL: base,
        FIELD_BOOTSTRAP_URL: f"{base}/bootstrap",
        "project_url_template": f"{base}/projects/{{project_id}}",
    }


def _project_url(base: str, project_id: object) -> str:
    return f"{base}/projects/{project_id}"


def _manual_test_data(directory: Path, state: dict[str, object]) -> dict[str, object]:
    run_id = str(state[FIELD_RUN_ID])
    fixtures = fixture_descriptors(run_id)
    isolation = fixtures[FIXTURE_ISOLATION]
    projects = isolation["projects"]
    atlas, orion = projects
    base = str(state[FIELD_SIGN_IN_URL])
    administrator_username = isolation[FIELD_ADMINISTRATOR][FIELD_USERNAME]
    urls = {
        URL_SIGN_IN: base,
        "overview": base,
        "bootstrap": str(state[FIELD_BOOTSTRAP_URL]),
        URL_AUDIT: f"{base}/audit",
        "atlas_project": _project_url(base, atlas["id"]),
        "orion_project": _project_url(base, orion["id"]),
        "unknown_project": _project_url(base, UNKNOWN_PROJECT_ID),
    }
    password_path = directory / PASSWORD_FILE
    return {
        "schema_version": "1.0",
        FIELD_RUN_ID: run_id,
        FIELD_CANDIDATE_COMMIT: state[FIELD_CANDIDATE_COMMIT],
        "session_status": state[FIELD_STATUS],
        "active_fixture": state[FIELD_FIXTURE],
        FIELD_URLS: urls,
        "credentials": {
            "bootstrap_username": "admin.bootstrap",
            FIELD_ADMINISTRATOR_USERNAME: administrator_username,
            FIELD_ADMINISTRATOR_PASSWORD: {
                "secret": True,
                "source_file": str(password_path) if password_path.is_file() else None,
                "json_field": FIELD_PASSWORD,
            },
        },
        "projects": {
            "atlas": atlas,
            "orion": orion,
            "unknown": {"id": UNKNOWN_PROJECT_ID},
        },
        "test_cases": {
            "MT-PRC-01-001": {
                FIELD_FIXTURE: FIXTURE_FRESH,
                FIELD_URLS: [urls[URL_SIGN_IN], urls["bootstrap"], urls[URL_AUDIT]],
                "bootstrap_username": "admin.bootstrap",
            },
            "MT-PRC-01-002": {
                FIELD_FIXTURE: FIXTURE_ADMIN_NO_PROJECT,
                FIELD_URLS: [urls[URL_SIGN_IN], urls["bootstrap"], urls[URL_AUDIT]],
                FIELD_ADMINISTRATOR_USERNAME: administrator_username,
            },
            "MT-PRC-01-003": {
                FIELD_FIXTURE: FIXTURE_ADMIN_NO_PROJECT,
                FIELD_URLS: [urls[URL_SIGN_IN]],
                FIELD_USERNAME: "missing.user",
                FIELD_PASSWORD: "Invalid-Only-For-Test-01!",
            },
            "MT-PRC-01-004": {
                FIELD_FIXTURE: FIXTURE_ISOLATION,
                FIELD_URLS: [
                    urls[URL_SIGN_IN],
                    urls["atlas_project"],
                    urls[URL_AUDIT],
                ],
                FIELD_ADMINISTRATOR_USERNAME: administrator_username,
            },
            "MT-PRC-01-005": {
                FIELD_FIXTURE: FIXTURE_ADMIN_NO_PROJECT,
                FIELD_URLS: [urls[URL_SIGN_IN], urls[URL_AUDIT]],
                FIELD_ADMINISTRATOR_USERNAME: administrator_username,
                "project_name": atlas["name"],
                "project_key": atlas["key"],
            },
            "MT-PRC-01-006": {
                FIELD_FIXTURE: FIXTURE_ISOLATION,
                FIELD_URLS: [
                    urls[URL_SIGN_IN],
                    urls["atlas_project"],
                    urls["orion_project"],
                    urls["unknown_project"],
                ],
                FIELD_ADMINISTRATOR_USERNAME: administrator_username,
            },
        },
    }


def _write_manual_test_data(directory: Path, state: dict[str, object]) -> None:
    _write_json(directory / TEST_DATA_FILE, _manual_test_data(directory, state))


def _initial_state(
    manifest: dict[str, object], run_id: str, api_port: int, web_port: int
) -> dict[str, object]:
    images = manifest[FIELD_IMAGES]
    return {
        FIELD_STATUS: "STARTING",
        FIELD_RUN_ID: run_id,
        FIELD_CANDIDATE_COMMIT: manifest["source_commit"],
        "compose_project": f"apistra-cap01-{run_id}",
        "environment": f"local-staging-{run_id}",
        "api_image": images["api"][FIELD_REFERENCE],
        "worker_image": images["worker"][FIELD_REFERENCE],
        "web_image": images["web"][FIELD_REFERENCE],
        "api_port": api_port,
        "web_port": web_port,
        FIELD_FIXTURE: None,
        "fixture_attempt": 0,
        "started_at": _utc_now(),
        **_session_urls(web_port),
    }


def _load_state(run_id: str) -> tuple[Path, dict[str, object]]:
    directory = session_directory(run_id)
    state = _read_json(directory / SESSION_FILE)
    return directory, state


def _load_private(directory: Path) -> dict[str, object]:
    return _read_json(directory / SECRET_FILE)


def _existing_run_error(directory: Path, run_id: str) -> ManualAcceptanceError:
    session_path = directory / SESSION_FILE
    if not session_path.is_file():
        detail = "the evidence directory exists without a readable session record"
    else:
        try:
            status_value = _read_json(session_path).get(FIELD_STATUS, "UNKNOWN")
            detail = f"the existing session has status {status_value}"
        except (OSError, ValueError, TypeError):
            detail = "the existing session record cannot be read"
    return ManualAcceptanceError(
        f"run ID '{run_id}' already exists and must not be overwritten; {detail}. "
        "Choose a new run ID and retain the existing evidence directory."
    )


def _create_session_directory(run_id: str) -> Path:
    directory = session_directory(run_id)
    try:
        directory.mkdir(parents=True, mode=OWNER_DIRECTORY_MODE, exist_ok=False)
    except FileExistsError:
        raise _existing_run_error(directory, run_id) from None
    return directory


def _record_fixture(
    directory: Path,
    state: dict[str, object],
    receipt: dict[str, object],
    fixture: str,
) -> None:
    attempt = int(state["fixture_attempt"]) + 1
    receipt_path = directory / f"fixture-{attempt:02d}-{fixture}.json"
    _write_json(receipt_path, receipt)
    state.update(
        {
            FIELD_STATUS: RUNNING,
            FIELD_FIXTURE: fixture,
            "fixture_attempt": attempt,
            "fixture_receipt": receipt_path.name,
            "updated_at": _utc_now(),
        }
    )
    _write_json(directory / SESSION_FILE, state)


def _apply_fixture(
    directory: Path,
    state: dict[str, object],
    private: dict[str, object],
    fixture: str,
) -> dict[str, object]:
    env = _environment(state, private)
    if fixture != FIXTURE_FRESH:
        env["STAGING_ADMIN_PASSWORD"] = str(private[FIELD_ADMINISTRATOR_PASSWORD])
    receipt = apply_cap01_fixture(
        _compose_command(), env, str(state[FIELD_RUN_ID]), fixture
    )
    _record_fixture(directory, state, receipt, fixture)
    _write_manual_test_data(directory, state)
    return receipt


def _verify_deployment(state: dict[str, object]) -> None:
    commit = state[FIELD_CANDIDATE_COMMIT]
    api = wait_for(f"http://127.0.0.1:{state['api_port']}/health/ready", "ready")
    web = wait_for(f"http://127.0.0.1:{state['web_port']}/api/health", "ready")
    if api["deployment"]["commit"] != commit or web["deployment"]["commit"] != commit:
        raise RuntimeError("deployment marker does not match the candidate commit")


def _public_summary(directory: Path, state: dict[str, object]) -> dict[str, object]:
    password_path = directory / PASSWORD_FILE
    return {
        FIELD_STATUS: state[FIELD_STATUS],
        FIELD_RUN_ID: state[FIELD_RUN_ID],
        FIELD_CANDIDATE_COMMIT: state[FIELD_CANDIDATE_COMMIT],
        FIELD_FIXTURE: state[FIELD_FIXTURE],
        FIELD_SIGN_IN_URL: state[FIELD_SIGN_IN_URL],
        FIELD_BOOTSTRAP_URL: state[FIELD_BOOTSTRAP_URL],
        "project_url_template": state["project_url_template"],
        "password_file": str(password_path) if password_path.is_file() else None,
        "test_data_file": str(directory / TEST_DATA_FILE),
        "evidence_directory": str(directory),
    }


def start(args: argparse.Namespace) -> int:
    """Start one candidate and prepare the requested deterministic fixture."""

    directory = _create_session_directory(args.run_id)
    manifest = _read_json(args.manifest)
    state = _initial_state(manifest, args.run_id, args.api_port, args.web_port)
    private = {
        "database_password": secrets.token_urlsafe(DATABASE_PASSWORD_BYTES),
        FIELD_ADMINISTRATOR_PASSWORD: secrets.token_urlsafe(24),
    }
    _write_json(directory / SESSION_FILE, state)
    _write_private_json(directory / SECRET_FILE, private)
    write_container_secret_json(
        directory / KEY_RING_FILE,
        {
            "keys": {
                SECRET_KEY_ID: base64.urlsafe_b64encode(
                    secrets.token_bytes(SECRET_KEY_BYTES)
                ).decode("ascii")
            }
        },
    )
    password_path = directory / PASSWORD_FILE
    _write_private_json(
        password_path,
        {
            FIELD_USERNAME: "admin.alpha",
            FIELD_PASSWORD: private[FIELD_ADMINISTRATOR_PASSWORD],
        },
    )
    env = _environment(state, private)
    try:
        run([*_compose_command(), "up", "--detach", "--wait"], env)
        _verify_deployment(state)
        _apply_fixture(directory, state, private, args.fixture)
    except Exception:
        run(
            [*_compose_command(), "down", "--volumes", "--remove-orphans"],
            env,
            check=False,
        )
        state.update({FIELD_STATUS: "FAILED", "updated_at": _utc_now()})
        _write_json(directory / SESSION_FILE, state)
        (directory / SECRET_FILE).unlink(missing_ok=True)
        (directory / KEY_RING_FILE).unlink(missing_ok=True)
        password_path.unlink(missing_ok=True)
        raise
    print(json.dumps(_public_summary(directory, state), sort_keys=True))
    return 0


def fixture(args: argparse.Namespace) -> int:
    """Reset the running session to one named fixture and retain its receipt."""

    directory, state = _load_state(args.run_id)
    private = _load_private(directory)
    if state[FIELD_STATUS] != RUNNING:
        raise RuntimeError("manual acceptance session is not running")
    _verify_deployment(state)
    receipt = _apply_fixture(directory, state, private, args.fixture)
    print(json.dumps(receipt, sort_keys=True))
    return 0


def status(args: argparse.Namespace) -> int:
    """Print secret-free identity and health details for one session."""

    directory, state = _load_state(args.run_id)
    if state[FIELD_STATUS] == RUNNING:
        _verify_deployment(state)
    print(json.dumps(_public_summary(directory, state), sort_keys=True))
    return 0


def stop(args: argparse.Namespace) -> int:
    """Remove the isolated runtime and delete its local secret material."""

    directory, state = _load_state(args.run_id)
    if state[FIELD_STATUS] == STOPPED:
        print(json.dumps(_public_summary(directory, state), sort_keys=True))
        return 0
    private = _load_private(directory)
    env = _environment(state, private)
    run(
        [*_compose_command(), "down", "--volumes", "--remove-orphans"],
        env,
        check=False,
    )
    (directory / SECRET_FILE).unlink(missing_ok=True)
    (directory / KEY_RING_FILE).unlink(missing_ok=True)
    (directory / PASSWORD_FILE).unlink(missing_ok=True)
    state.update({FIELD_STATUS: STOPPED, "stopped_at": _utc_now()})
    _write_json(directory / SESSION_FILE, state)
    _write_manual_test_data(directory, state)
    print(json.dumps(_public_summary(directory, state), sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line contract."""

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    start_parser = commands.add_parser("start")
    start_parser.add_argument("manifest", type=Path)
    start_parser.add_argument(ARG_RUN_ID, required=True)
    start_parser.add_argument("--fixture", choices=FIXTURES, default=FIXTURE_FRESH)
    start_parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    start_parser.add_argument("--web-port", type=int, default=DEFAULT_WEB_PORT)
    start_parser.set_defaults(handler=start)

    fixture_parser = commands.add_parser("fixture")
    fixture_parser.add_argument("fixture", choices=FIXTURES)
    fixture_parser.add_argument(ARG_RUN_ID, required=True)
    fixture_parser.set_defaults(handler=fixture)

    status_parser = commands.add_parser("status")
    status_parser.add_argument(ARG_RUN_ID, required=True)
    status_parser.set_defaults(handler=status)

    stop_parser = commands.add_parser("stop")
    stop_parser.add_argument(ARG_RUN_ID, required=True)
    stop_parser.set_defaults(handler=stop)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args))
    except ManualAcceptanceError as error:
        print(f"Manual acceptance command failed safely: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
