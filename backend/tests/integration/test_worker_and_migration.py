import json
import sys
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from apistra.entrypoints import migration
from apistra.entrypoints.worker import main as worker
from apistra.platform.runtime import RuntimeSettings


def test_worker_heartbeat_is_healthy(tmp_path: Path) -> None:
    path = tmp_path / "heartbeat.json"
    settings = RuntimeSettings("worker", "0.0.1", "abc", "test")
    worker.write_heartbeat(path, settings)
    assert worker.heartbeat_is_healthy(path)


def test_worker_rejects_forced_not_ready_heartbeat(tmp_path: Path) -> None:
    path = tmp_path / "heartbeat.json"
    settings = RuntimeSettings("worker", "0.0.1", "abc", "test", force_not_ready=True)
    worker.write_heartbeat(path, settings)
    assert not worker.heartbeat_is_healthy(path)


def test_worker_rejects_stale_heartbeat(tmp_path: Path) -> None:
    path = tmp_path / "heartbeat.json"
    stale = datetime.now(UTC) - timedelta(minutes=1)
    path.write_text(json.dumps({"status": "ready", "observed_at": stale.isoformat()}))
    assert not worker.heartbeat_is_healthy(path, max_age_seconds=10)


def test_worker_rejects_missing_and_invalid_heartbeat(tmp_path: Path) -> None:
    path = tmp_path / "heartbeat.json"
    assert not worker.heartbeat_is_healthy(path)
    path.write_text("not-json", encoding="utf-8")
    assert not worker.heartbeat_is_healthy(path)


@pytest.mark.migration
def test_migration_is_an_idempotent_noop() -> None:
    assert migration.migration_result() == migration.migration_result()
    assert migration.migration_result()["applied"] == []


@pytest.mark.migration
def test_migration_cli_emits_json(capsys) -> None:
    assert migration.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "up_to_date"


def test_worker_healthcheck_cli(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "heartbeat.json"
    worker.write_heartbeat(path, RuntimeSettings("worker", "1", "abc", "test"))
    monkeypatch.setenv("APISTRA_HEARTBEAT_PATH", str(path))
    monkeypatch.setattr(sys, "argv", ["worker", "--healthcheck"])
    assert worker.main() == 0


def test_worker_run_writes_before_sleep(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "heartbeat.json"
    monkeypatch.setenv("APISTRA_HEARTBEAT_PATH", str(path))

    def stop(_interval: float) -> None:
        raise StopIteration

    monkeypatch.setattr(worker.time, "sleep", stop)
    with suppress(StopIteration):
        worker.run(interval_seconds=0)
    assert path.exists()
