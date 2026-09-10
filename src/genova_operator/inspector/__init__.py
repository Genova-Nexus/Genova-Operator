"""Genova Operator Project Inspector Package (`Project Inspector`).

Provides structured inspection of registered and discovered projects, including directory
hierarchy, dependencies, Git repository status, runtime environment, and entry points.
"""

from genova_operator.inspector.manager import ProjectInspector
from genova_operator.inspector.models import (
    DependencySummary,
    DirectoryNode,
    DirectoryTree,
    EntryPointsSummary,
    EnvironmentInspection,
    ProjectInspectionReport,
    RepositoryInspection,
)

__all__ = [
    "ProjectInspector",
    "ProjectInspectionReport",
    "DirectoryTree",
    "DirectoryNode",
    "DependencySummary",
    "RepositoryInspection",
    "EnvironmentInspection",
    "EntryPointsSummary",
]
