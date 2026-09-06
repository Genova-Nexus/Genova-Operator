"""Workspace data models for Genova Operator.

Defines workspace status, workspace info, and workspace health data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class WorkspaceStatus(Enum):
    """Status of the Genova workspace environment."""
    UNINITIALIZED = "UNINITIALIZED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"


@dataclass
class WorkspaceHealth:
    """Diagnostic report of the workspace health.

    Attributes:
        exists: True if workspace root path exists.
        is_directory: True if root path is a directory.
        writable: True if workspace root path has write permissions.
        projects_dir_exists: True if projects directory exists.
        has_marker: True if workspace marker file exists.
        free_bytes: Optional free storage space in bytes.
        message: Human-readable status message.
    """
    exists: bool = False
    is_directory: bool = False
    writable: bool = False
    projects_dir_exists: bool = False
    has_marker: bool = False
    free_bytes: Optional[int] = None
    message: str = ""

    @property
    def is_healthy(self) -> bool:
        """Return True if root exists, is directory, and is writable."""
        return self.exists and self.is_directory and self.writable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exists": self.exists,
            "is_directory": self.is_directory,
            "writable": self.writable,
            "projects_dir_exists": self.projects_dir_exists,
            "has_marker": self.has_marker,
            "free_bytes": self.free_bytes,
            "is_healthy": self.is_healthy,
            "message": self.message,
        }


@dataclass
class WorkspaceInfo:
    """Information summary about the Genova workspace boundaries and locations.

    Attributes:
        name: Name or label of the workspace.
        root_path: Relative or raw workspace root path string.
        absolute_root_path: Absolute resolved Path string.
        projects_dir_path: Absolute resolved projects directory Path string.
        has_marker: True if workspace marker file exists.
        status: Current WorkspaceStatus.
        candidate_projects: List of detected candidate project directory names.
        metadata: Arbitrary workspace metadata.
    """
    name: str = "genova-workspace"
    root_path: str = "."
    absolute_root_path: str = ""
    projects_dir_path: str = ""
    has_marker: bool = False
    status: WorkspaceStatus = WorkspaceStatus.UNINITIALIZED
    candidate_projects: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root_path": self.root_path,
            "absolute_root_path": self.absolute_root_path,
            "projects_dir_path": self.projects_dir_path,
            "has_marker": self.has_marker,
            "status": self.status.value,
            "candidate_projects": self.candidate_projects,
            "metadata": self.metadata,
        }
