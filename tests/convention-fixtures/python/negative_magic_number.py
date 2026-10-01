"""Negative fixture proving that unnamed numeric policy values are rejected."""


def calculate_limit(value: int) -> int:
    """Apply an intentionally unnamed policy value."""

    return value * 42
