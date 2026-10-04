"""Idempotent database migration entrypoint."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

MIGRATIONS_ROOT = Path(__file__).resolve().parents[1] / "platform/database/migrations"


def apply_migrations(dsn: str) -> list[str]:
    """Apply immutable SQL migrations in lexical order and return newly applied IDs."""

    applied: list[str] = []
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS apistra_schema_migrations (
                migration_id TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for path in sorted(MIGRATIONS_ROOT.glob("*/*.sql")):
            migration_id = f"{path.parent.name}/{path.stem}"
            cursor.execute(
                "SELECT 1 FROM apistra_schema_migrations WHERE migration_id = %s",
                (migration_id,),
            )
            if cursor.fetchone():
                continue
            cursor.execute(path.read_text(encoding="utf-8"))
            cursor.execute(
                """
                INSERT INTO apistra_schema_migrations (migration_id)
                VALUES (%s) ON CONFLICT (migration_id) DO NOTHING
                """,
                (migration_id,),
            )
            applied.append(migration_id)
    return applied


def migration_result() -> dict[str, object]:
    dsn = os.getenv("APISTRA_DATABASE_URL")
    applied = apply_migrations(dsn) if dsn else []
    return {
        "status": "up_to_date",
        "schema_version": "cap02-secret-references" if dsn else "cap00-none",
        "commit": os.getenv("APISTRA_COMMIT", "unknown"),
        "applied": applied,
    }


def main() -> int:
    print(json.dumps(migration_result(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
