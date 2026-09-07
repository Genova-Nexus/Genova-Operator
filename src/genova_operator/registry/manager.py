"""ProjectRegistry component for Genova Operator.

Acts as the central source of truth for registered Genova projects.
Implements BaseProjectRegistry and BaseComponent interfaces with thread safety,
lookup capabilities, and persistence.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.core.exceptions import (
    GenovaOperatorError,
    ProjectNotFoundError,
)
from genova_operator.core.interfaces import BaseComponent, BaseProjectRegistry
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.registry.models import (
    EnvironmentInfo,
    ProjectIdentity,
    ProjectRecord,
    RepositoryInfo,
)

logger = logging.getLogger(__name__)


class ProjectRegistry(BaseComponent, BaseProjectRegistry):
    """Central project registry component for Genova Operator.

    Stores, manages, and persists ProjectRecord information for projects like
    GeneFusionAI, Clarify, and future ecosystem additions.
    """

    def __init__(self, name: str = "project-registry", registry_file: Optional[Union[str, Path]] = None) -> None:
        self._name = name
        self._registry_file = Path(registry_file) if registry_file else None
        self._projects: Dict[str, ProjectRecord] = {}
        self._lock = threading.RLock()
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize the project registry and load persisted records if available."""
        logger.info("Initializing ProjectRegistry (%s)...", self._name)
        try:
            if self._registry_file and self._registry_file.is_file():
                self.load_from_file(self._registry_file)

            self._status = OperatorStatus.READY
            logger.info("ProjectRegistry initialized successfully with %d projects.", len(self._projects))
        except Exception as err:
            self._status = OperatorStatus.ERROR
            raise GenovaOperatorError(f"Failed to initialize ProjectRegistry: {err}") from err

    def shutdown(self) -> None:
        """Shutdown ProjectRegistry, saving state if file path configured."""
        with self._lock:
            if self._registry_file:
                try:
                    self.save_to_file(self._registry_file)
                except Exception as err:
                    logger.error("Error saving registry on shutdown: %s", err)
            self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def register_project(
        self,
        name: str,
        path: str = ".",
        config: Optional[Dict[str, Any]] = None,
        project_record: Optional[ProjectRecord] = None,
    ) -> ProjectRecord:
        """Register a new project or update an existing project record.

        Args:
            name: Short project name identifier.
            path: Project filesystem root path.
            config: Optional config options or parameters dictionary.
            project_record: Pre-constructed ProjectRecord object.

        Returns:
            The registered ProjectRecord instance.
        """
        with self._lock:
            if project_record is not None:
                record = project_record
            elif name in self._projects:
                # Update existing record
                record = self._projects[name]
                record.path = path
                if config:
                    record.options.update(config)
                record.last_active_at = time.time()
            else:
                identity = ProjectIdentity(name=name, display_name=name)
                record = ProjectRecord(
                    identity=identity,
                    path=path,
                    options=config or {},
                )

            self._projects[record.name] = record
            logger.info("Registered project '%s' at path '%s'.", record.name, record.path)
            return record

    def unregister_project(self, name: str) -> bool:
        """Remove a project from the registry.

        Args:
            name: Project name identifier.

        Returns:
            True if project was found and removed, False otherwise.
        """
        with self._lock:
            if name in self._projects:
                del self._projects[name]
                logger.info("Unregistered project '%s'.", name)
                return True
            return False

    def get_project(self, name: str) -> Optional[ProjectRecord]:
        """Retrieve project record by name.

        Args:
            name: Project name.

        Returns:
            ProjectRecord instance if found, or None.
        """
        with self._lock:
            record = self._projects.get(name)
            if record:
                record.last_active_at = time.time()
            return record

    def get_project_or_raise(self, name: str) -> ProjectRecord:
        """Retrieve project record by name or raise ProjectNotFoundError."""
        record = self.get_project(name)
        if not record:
            raise ProjectNotFoundError(f"Project '{name}' is not registered in ProjectRegistry.")
        return record

    def has_project(self, name: str) -> bool:
        """Return True if project name is registered."""
        with self._lock:
            return name in self._projects

    def list_projects(self, project_type: Optional[str] = None) -> Dict[str, ProjectRecord]:
        """List all registered projects, optionally filtered by project_type.

        Returns:
            Dictionary mapping project names to ProjectRecord objects.
        """
        with self._lock:
            if project_type:
                return {
                    name: proj
                    for name, proj in self._projects.items()
                    if proj.identity.project_type == project_type
                }
            return dict(self._projects)

    def count(self) -> int:
        """Return total number of registered projects."""
        with self._lock:
            return len(self._projects)

    def clear(self) -> None:
        """Clear all registered project records."""
        with self._lock:
            self._projects.clear()

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save all project records to a JSON registry file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = {name: proj.to_dict() for name, proj in self._projects.items()}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Saved ProjectRegistry state to '%s'.", path)

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load project records from a JSON registry file."""
        path = Path(file_path)
        if not path.is_file():
            raise GenovaOperatorError(f"Registry file not found: '{path}'")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with self._lock:
            self._projects.clear()
            for name, proj_data in data.items():
                self._projects[name] = ProjectRecord.from_dict(proj_data)
            logger.info("Loaded %d projects from '%s'.", len(self._projects), path)
