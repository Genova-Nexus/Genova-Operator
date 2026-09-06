"""Genova Operator Workspace Package (`Workspace Manager`).

Provides workspace environment identification, path boundary enforcement,
health diagnostics, and project directory discovery.
"""

from genova_operator.workspace.manager import (
    WorkspaceBoundaryError,
    WorkspaceManager,
)
from genova_operator.workspace.models import (
    WorkspaceHealth,
    WorkspaceInfo,
    WorkspaceStatus,
)

__all__ = [
    "WorkspaceManager",
    "WorkspaceBoundaryError",
    "WorkspaceInfo",
    "WorkspaceHealth",
    "WorkspaceStatus",
]
