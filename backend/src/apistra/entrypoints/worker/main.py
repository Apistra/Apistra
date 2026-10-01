"""Long-running CAP-00 worker shell with a file-based heartbeat."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from apistra.platform.observability.logging import configure_logging, log_event
from apistra.platform.runtime import RuntimeSettings

DEFAULT_HEARTBEAT_MAX_AGE_SECONDS = 15.0


def write_heartbeat(path: Path, settings: RuntimeSettings) -> None:
    payload = {
        "status": "not_ready" if settings.force_not_ready else "ready",
        "observed_at": datetime.now(UTC).isoformat(),
        "deployment": settings.marker(),
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def heartbeat_is_healthy(
    path: Path, max_age_seconds: float = DEFAULT_HEARTBEAT_MAX_AGE_SECONDS
) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = datetime.fromisoformat(payload["observed_at"])
    except (FileNotFoundError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return False
    age = (datetime.now(UTC) - observed).total_seconds()
    return payload.get("status") == "ready" and 0 <= age <= max_age_seconds


def run(interval_seconds: float = 5.0) -> None:
    settings = RuntimeSettings.from_environment("worker")
    path = Path(settings.heartbeat_path)
    configure_logging()
    log_event("worker.started", deployment=settings.marker())
    while True:
        write_heartbeat(path, settings)
        time.sleep(interval_seconds)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--healthcheck", action="store_true")
    parser.add_argument(
        "--max-age-seconds",
        type=float,
        default=DEFAULT_HEARTBEAT_MAX_AGE_SECONDS,
    )
    args = parser.parse_args()
    settings = RuntimeSettings.from_environment("worker")
    if args.healthcheck:
        return 0 if heartbeat_is_healthy(Path(settings.heartbeat_path), args.max_age_seconds) else 1
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
