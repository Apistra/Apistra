"""Negative fixture proving that repeated semantic strings are rejected."""


def build_payload() -> tuple[str, str, str, str]:
    """Return an intentionally invalid payload."""

    return ("project-status", "project-status", "project-status", "project-status")
