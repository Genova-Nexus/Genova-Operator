"""ProjectDiscovery component for Genova Operator.

Automates the discovery of Genova software and research projects within configured
workspaces, evaluating confidence and auto-registering them into ProjectRegistry.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.core.exceptions import GenovaOperatorError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.discovery.models import DiscoveredProject, ProjectConfidence
from genova_operator.discovery.rules import evaluate_directory
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import ProjectRecord
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class ProjectDiscovery(BaseComponent):
    """Project Discovery component for Genova Operator.

    Identifies software and ML research projects in workspace locations.
    """

    def __init__(
        self,
        name: str = "project-discovery",
        workspace_manager: Optional[WorkspaceManager] = None,
        project_registry: Optional[ProjectRegistry] = None,
    ) -> None:
        self._name = name
        self._workspace_manager = workspace_manager
        self._project_registry = project_registry
        self._status = OperatorStatus.UNINITIALIZED
        self._discovered_projects: Dict[str, DiscoveredProject] = {}

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize the ProjectDiscovery component."""
        logger.info("Initializing ProjectDiscovery (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("ProjectDiscovery initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectDiscovery."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def inspect_directory(self, dir_path: Union[str, Path]) -> DiscoveredProject:
        """Inspect a single directory and return a DiscoveredProject object.

        Args:
            dir_path: Directory path to inspect.

        Returns:
            DiscoveredProject object.
        """
        path = Path(dir_path).resolve()
        confidence, project_type, matched_rules, metadata = evaluate_directory(path)

        project_name = metadata.get("custom_name", path.name)
        entry_points = metadata.get("entry_points", {})

        discovered = DiscoveredProject(
            name=project_name,
            path=str(path),
            confidence=confidence,
            project_type=project_type,
            matched_rules=matched_rules,
            detected_entry_points=entry_points,
            metadata=metadata,
        )
        return discovered

    def discover_projects(
        self,
        scan_path: Optional[Union[str, Path]] = None,
        min_confidence: ProjectConfidence = ProjectConfidence.MEDIUM,
    ) -> List[DiscoveredProject]:
        """Scan a directory (or workspace projects directory) and return matching projects.

        Args:
            scan_path: Directory path to scan. Defaults to workspace projects path.
            min_confidence: Minimum ProjectConfidence threshold to include.

        Returns:
            List of DiscoveredProject instances matching min_confidence.
        """
        if scan_path is not None:
            target_dir = Path(scan_path).resolve()
        elif self._workspace_manager is not None:
            target_dir = self._workspace_manager.projects_path
        else:
            target_dir = Path(".").resolve()

        if not target_dir.exists() or not target_dir.is_dir():
            logger.warning("Scan directory '%s' does not exist or is not a directory.", target_dir)
            return []

        results: List[DiscoveredProject] = []
        self._discovered_projects.clear()

        logger.info("Scanning for projects in '%s' (min_confidence: %s)...", target_dir, min_confidence.value)

        # Inspect candidate subdirectories
        for entry in target_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith((".", "_")):
                discovered = self.inspect_directory(entry)
                if discovered.confidence.score >= min_confidence.score:
                    results.append(discovered)
                    self._discovered_projects[discovered.name] = discovered
                    logger.info("Discovered project '%s' (confidence: %s).", discovered.name, discovered.confidence.value)

        return results

    def auto_register_discovered(
        self,
        registry: Optional[ProjectRegistry] = None,
        min_confidence: ProjectConfidence = ProjectConfidence.MEDIUM,
    ) -> List[ProjectRecord]:
        """Discover projects and automatically register them into ProjectRegistry.

        Args:
            registry: Target ProjectRegistry instance (uses self._project_registry if None).
            min_confidence: Minimum confidence threshold for registration.

        Returns:
            List of registered ProjectRecord objects.
        """
        target_registry = registry or self._project_registry
        if target_registry is None:
            raise GenovaOperatorError("Cannot auto-register projects. No ProjectRegistry provided.")

        discovered_list = self.discover_projects(min_confidence=min_confidence)
        registered_records: List[ProjectRecord] = []

        for project in discovered_list:
            record = project.to_project_record()
            target_registry.register_project(name=record.name, project_record=record)
            registered_records.append(record)
            logger.info("Auto-registered project '%s' into ProjectRegistry.", record.name)

        return registered_records
