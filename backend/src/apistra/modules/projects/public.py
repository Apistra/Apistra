"""Stable public contract of the projects module.

Cross-module callers may import this module, but not the module internals.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Verified project scope passed to project-owned use cases."""

    project_id: str
