"""Prepare and control a local CAP-01 manual acceptance session."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
from datetime import UTC, datetime
from pathlib import Path

from tools.staging.verify_candidate import (
    COMPOSE,
    DATABASE_PASSWORD_BYTES,
    DEFAULT_API_PORT,
    DEFAULT_WEB_PORT,
    FIELD_IMAGES,
    FIELD_REFERENCE,
    apply_cap01_fixture,
    run,
    wait_for,
)

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_ROOT = ROOT / "artifacts/acceptance/CAP-01"
SESSION_FILE = "session.json"
SECRET_FILE = "runtime-secrets.json"
UTF8 = "utf-8"
RUNNING = "RUNNING"
STOPPED = "STOPPED"
FIELD_STATUS = "status"
FIELD_RUN_ID = "run_id"
FIELD_CANDIDATE_COMMIT = "candidate_commit"
FIELD_FIXTURE = "fixture"
ARG_RUN_ID = "--run-id"
OWNER_ONLY_MODE = 0o600
OWNER_DIRECTORY_MODE = 0o700
FIXTURE_FRESH = "FX-PRC-01-FRESH"
FIXTURES = (
    FIXTURE_FRESH,
    "FX-PRC-01-ADMIN-NO-PROJECT",
    "FX-PRC-01-ISOLATION",
)
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


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
            "APISTRA_FIXTURE_GATE": f"apply-cap01-{state[FIELD_RUN_ID]}",
        }
    )
    return env


def _session_urls(web_port: int) -> dict[str, str]:
    base = f"http://127.0.0.1:{web_port}"
    return {
        "sign_in_url": base,
        "bootstrap_url": f"{base}/bootstrap",
        "project_url_template": f"{base}/projects/{{project_id}}",
    }


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


def _load_session(run_id: str) -> tuple[Path, dict[str, object], dict[str, object]]:
    directory = session_directory(run_id)
    state = _read_json(directory / SESSION_FILE)
    private = _read_json(directory / SECRET_FILE)
    return directory, state, private


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
        env["STAGING_ADMIN_PASSWORD"] = str(private["administrator_password"])
    receipt = apply_cap01_fixture(
        _compose_command(), env, str(state[FIELD_RUN_ID]), fixture
    )
    _record_fixture(directory, state, receipt, fixture)
    return receipt


def _verify_deployment(state: dict[str, object]) -> None:
    commit = state[FIELD_CANDIDATE_COMMIT]
    api = wait_for(f"http://127.0.0.1:{state['api_port']}/health/ready", "ready")
    web = wait_for(f"http://127.0.0.1:{state['web_port']}/api/health", "ready")
    if api["deployment"]["commit"] != commit or web["deployment"]["commit"] != commit:
        raise RuntimeError("deployment marker does not match the candidate commit")


def _public_summary(directory: Path, state: dict[str, object]) -> dict[str, object]:
    return {
        FIELD_STATUS: state[FIELD_STATUS],
        FIELD_RUN_ID: state[FIELD_RUN_ID],
        FIELD_CANDIDATE_COMMIT: state[FIELD_CANDIDATE_COMMIT],
        FIELD_FIXTURE: state[FIELD_FIXTURE],
        "sign_in_url": state["sign_in_url"],
        "bootstrap_url": state["bootstrap_url"],
        "project_url_template": state["project_url_template"],
        "password_file": str(directory / "staging-admin-password.txt"),
        "evidence_directory": str(directory),
    }


def start(args: argparse.Namespace) -> int:
    """Start one candidate and prepare the requested deterministic fixture."""

    directory = session_directory(args.run_id)
    directory.mkdir(parents=True, mode=OWNER_DIRECTORY_MODE, exist_ok=False)
    manifest = _read_json(args.manifest)
    state = _initial_state(manifest, args.run_id, args.api_port, args.web_port)
    private = {
        "database_password": secrets.token_urlsafe(DATABASE_PASSWORD_BYTES),
        "administrator_password": secrets.token_urlsafe(24),
    }
    _write_json(directory / SESSION_FILE, state)
    _write_private_json(directory / SECRET_FILE, private)
    password_path = directory / "staging-admin-password.txt"
    _write_private_json(
        password_path,
        {"username": "admin.alpha", "password": private["administrator_password"]},
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
        password_path.unlink(missing_ok=True)
        raise
    print(json.dumps(_public_summary(directory, state), sort_keys=True))
    return 0


def fixture(args: argparse.Namespace) -> int:
    """Reset the running session to one named fixture and retain its receipt."""

    directory, state, private = _load_session(args.run_id)
    if state[FIELD_STATUS] != RUNNING:
        raise RuntimeError("manual acceptance session is not running")
    _verify_deployment(state)
    receipt = _apply_fixture(directory, state, private, args.fixture)
    print(json.dumps(receipt, sort_keys=True))
    return 0


def status(args: argparse.Namespace) -> int:
    """Print secret-free identity and health details for one session."""

    directory, state, _private = _load_session(args.run_id)
    if state[FIELD_STATUS] == RUNNING:
        _verify_deployment(state)
    print(json.dumps(_public_summary(directory, state), sort_keys=True))
    return 0


def stop(args: argparse.Namespace) -> int:
    """Remove the isolated runtime and delete its local secret material."""

    directory, state, private = _load_session(args.run_id)
    env = _environment(state, private)
    run(
        [*_compose_command(), "down", "--volumes", "--remove-orphans"],
        env,
        check=False,
    )
    (directory / SECRET_FILE).unlink(missing_ok=True)
    (directory / "staging-admin-password.txt").unlink(missing_ok=True)
    state.update({FIELD_STATUS: STOPPED, "stopped_at": _utc_now()})
    _write_json(directory / SESSION_FILE, state)
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
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
