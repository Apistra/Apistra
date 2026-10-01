"""Positive Python convention fixture."""

from typing import Final

MAXIMUM_ATTEMPTS: Final = 3
RESULT_FIELD: Final = "result"


def create_results(value: str) -> dict[str, str]:
    """Return a typed result using named contract values."""

    return {RESULT_FIELD: value * MAXIMUM_ATTEMPTS}
