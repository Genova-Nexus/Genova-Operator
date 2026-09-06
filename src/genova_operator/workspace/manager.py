"""WorkspaceManager component for Genova Operator.

Manages workspace boundaries, directory path resolution, health diagnostics,
candidate project scanning, and workspace markers.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.config.manager import ConfigManager
from genova_operator.core.exceptions import GenovaOperatorError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.workspace.models import (
    WorkspaceHealth,
    WorkspaceInfo,
    WorkspaceStatus,
)

logger = logging.getLogger(__name__)

MARKER_FILENAME = "genova_workspace.json"
DOT_MARKER_RELATIVE_PATH = ".genova/workspace.json"


class WorkspaceBoundaryError(GenovaOperatorError):
    """Raised when a path is outside configured workspace boundaries."""
    pass


class WorkspaceManager(BaseComponent):
    """Workspace Manager component for Genova Operator.

    Identifies workspace environment, resolves directory paths, enforces boundaries,
    runs health diagnostics, and locates candidate project directories.
    """

    def __init__(
        self,
        root_path: Union[str, Path] = ".",
        projects_dir: str = "projects",
        name: str = "workspace-manager",
        config_manager: Optional[ConfigManager] = None,
    ) -> None:
        self._name = name
        self._config_manager = config_manager
        self._root_path = Path(root_path)
        self._projects_dir = projects_dir
        self._status = OperatorStatus.UNINITIALIZED
        self._workspace_status = WorkspaceStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    @property
    def root_path(self) -> Path:
        """Return resolved absolute workspace root path."""
        if self._config_manager and self._config_manager.config:
            return Path(self._config_manager.config.workspace.root_path).resolve()
        return self._root_path.resolve()

    @property
    def projects_dir_name(self) -> str:
        """Return projects directory relative folder name."""
        if self._config_manager and self._config_manager.config:
            return self._config_manager.config.workspace.projects_dir
        return self._projects_dir

    @property
    def projects_path(self) -> Path:
        """Return resolved absolute path to workspace projects directory."""
        return (self.root_path / self.projects_dir_name).resolve()

    def initialize(self) -> None:
        """Initialize the workspace manager and check workspace boundaries."""
        logger.info("Initializing WorkspaceManager (%s)...", self._name)
        try:
            health = self.check_health()
            if health.is_healthy:
                self._workspace_status = WorkspaceStatus.ACTIVE
            else:
                self._workspace_status = WorkspaceStatus.DEGRADED

            self._status = OperatorStatus.READY
            logger.info("WorkspaceManager initialized at '%s' (status: %s).", self.root_path, self._workspace_status.value)
        except Exception as err:
            self._status = OperatorStatus.ERROR
            self._workspace_status = WorkspaceStatus.INVALID
            raise GenovaOperatorError(f"Failed to initialize WorkspaceManager: {err}") from err

    def shutdown(self) -> None:
        """Shutdown WorkspaceManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def resolve_path(self, target_path: Union[str, Path], enforce_boundary: bool = True) -> Path:
        """Resolve a relative or absolute path and verify workspace boundary safety.

        Args:
            target_path: Path string or Path object to resolve.
            enforce_boundary: If True, raise WorkspaceBoundaryError if path falls outside root.

        Returns:
            Resolved absolute Path.

        Raises:
            WorkspaceBoundaryError: If enforce_boundary is True and path is outside workspace.
        """
        path = Path(target_path)
        if not path.is_absolute():
            resolved = (self.root_path / path).resolve()
        else:
            resolved = path.resolve()

        if enforce_boundary and not self.is_within_workspace(resolved):
            raise WorkspaceBoundaryError(
                f"Path '{resolved}' is outside configured workspace root boundary '{self.root_path}'."
            )
        return resolved

    def is_within_workspace(self, target_path: Union[str, Path]) -> bool:
        """Return True if target_path falls within the workspace root directory."""
        try:
            resolved = Path(target_path).resolve()
            root = self.root_path
            return resolved == root or root in resolved.parents
        except Exception:
            return False

    def check_health(self) -> WorkspaceHealth:
        """Perform diagnostics on the workspace directory."""
        root = self.root_path
        exists = root.exists()
        is_dir = root.is_dir() if exists else False
        writable = os.access(root, os.W_OK) if exists else False
        projects_exists = self.projects_path.exists() and self.projects_path.is_dir()
        has_marker = self.has_marker()

        free_bytes: Optional[int] = None
        if exists:
            try:
                usage = shutil.disk_usage(root)
                free_bytes = usage.free
            except Exception:
                pass

        if not exists:
            msg = f"Workspace root directory '{root}' does not exist."
        elif not is_dir:
            msg = f"Workspace root '{root}' is not a directory."
        elif not writable:
            msg = f"Workspace root '{root}' is not writable."
        else:
            msg = f"Workspace at '{root}' is healthy."

        return WorkspaceHealth(
            exists=exists,
            is_directory=is_dir,
            writable=writable,
            projects_dir_exists=projects_exists,
            has_marker=has_marker,
            free_bytes=free_bytes,
            message=msg,
        )

    def has_marker(self) -> bool:
        """Check if workspace marker file exists (genova_workspace.json or .genova/workspace.json)."""
        marker1 = self.root_path / MARKER_FILENAME
        marker2 = self.root_path / DOT_MARKER_RELATIVE_PATH
        return marker1.is_file() or marker2.is_file()

    def create_marker(self, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Create or update a `.genova/workspace.json` marker file to define workspace boundary."""
        marker_dir = self.root_path / ".genova"
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker_file = marker_dir / "workspace.json"

        data = {
            "name": self.name,
            "root_path": str(self.root_path),
            "projects_dir": self.projects_dir_name,
            "metadata": metadata or {},
        }

        with open(marker_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info("Created workspace marker at '%s'.", marker_file)
        return marker_file

    def find_candidate_project_dirs(self) -> List[str]:
        """Scan the projects directory for candidate project directories."""
        p_dir = self.projects_path
        if not p_dir.exists() or not p_dir.is_dir():
            return []

        candidates = []
        for entry in p_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith((".", "_")):
                candidates.append(entry.name)
        return sorted(candidates)

    def get_info(self) -> WorkspaceInfo:
        """Return structured WorkspaceInfo summary object."""
        return WorkspaceInfo(
            name=self._name,
            root_path=str(self._root_path),
            absolute_root_path=str(self.root_path),
            projects_dir_path=str(self.projects_path),
            has_marker=self.has_marker(),
            status=self._workspace_status,
            candidate_projects=self.find_candidate_project_dirs(),
        )

    def ensure_structure(self) -> None:
        """Ensure workspace root and projects directories exist."""
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.projects_path.mkdir(parents=True, exist_ok=True)
