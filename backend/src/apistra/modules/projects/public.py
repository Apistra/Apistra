"""Stable public boundary of the projects module."""

from dataclasses import dataclass

from apistra.modules.projects.application import ProjectResult, ProjectService
from apistra.modules.projects.domain import Project, ProjectErrorCode, ProjectStatus


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Verified project scope passed to downstream project-owned use cases."""

    project_id: str


__all__ = [
    "Project",
    "ProjectContext",
    "ProjectErrorCode",
    "ProjectResult",
    "ProjectService",
    "ProjectStatus",
]
