"""Small structured logging adapter used by every CAP-00 process."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s", force=True)


def log_event(event: str, **fields: Any) -> None:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "event": event,
        **fields,
    }
    logging.getLogger("apistra").info(json.dumps(record, sort_keys=True, default=str))
