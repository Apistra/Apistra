"""Idempotent CAP-00 migration contract; there is no database schema yet."""

from __future__ import annotations

import json
import os


def migration_result() -> dict[str, object]:
    return {
        "status": "up_to_date",
        "schema_version": "cap00-none",
        "commit": os.getenv("APISTRA_COMMIT", "unknown"),
        "applied": [],
    }


def main() -> int:
    print(json.dumps(migration_result(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
