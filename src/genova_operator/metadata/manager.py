"""ProjectMetadataManager component for Genova Operator.

Manages metadata retrieval, update, auto-extraction from project files, and operational
support checking.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.core.exceptions import GenovaOperatorError, ProjectNotFoundError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.metadata.models import ProjectMetadata
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import ProjectRecord
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class ProjectMetadataManager(BaseComponent):
    """Project Metadata Manager component for Genova Operator.

    Stores, auto-extracts, and updates operational ProjectMetadata schemas for projects.
    """

    def __init__(
        self,
        name: str = "project-metadata",
        project_registry: Optional[ProjectRegistry] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._project_registry = project_registry
        self._workspace_manager = workspace_manager
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED
        self._metadata_store: Dict[str, ProjectMetadata] = {}

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize ProjectMetadataManager."""
        logger.info("Initializing ProjectMetadataManager (%s)...", self._name)
        if self._project_registry:
            for proj_name, record in self._project_registry.list_projects().items():
                if record.metadata and "purpose" in record.metadata:
                    self._metadata_store[proj_name] = ProjectMetadata.from_dict(record.metadata)
                else:
                    extracted = self.extract_metadata_from_project(record.path)
                    self._metadata_store[proj_name] = extracted

        self._status = OperatorStatus.READY
        logger.info("ProjectMetadataManager initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectMetadataManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def get_metadata(self, project_name: str) -> ProjectMetadata:
        """Retrieve ProjectMetadata for a project name.

        Args:
            project_name: Name of the project.

        Returns:
            ProjectMetadata instance.
        """
        if project_name not in self._metadata_store:
            if self._project_registry and self._project_registry.has_project(project_name):
                record = self._project_registry.get_project(project_name)
                if record:
                    extracted = self.extract_metadata_from_project(record.path)
                    self._metadata_store[project_name] = extracted
                    return extracted
            # Default empty metadata
            self._metadata_store[project_name] = ProjectMetadata()

        return self._metadata_store[project_name]

    def set_metadata(self, project_name: str, metadata: ProjectMetadata) -> None:
        """Set or update ProjectMetadata for a project.

        Args:
            project_name: Name of target project.
            metadata: ProjectMetadata object.
        """
        self._metadata_store[project_name] = metadata

        if self._project_registry and self._project_registry.has_project(project_name):
            record = self._project_registry.get_project(project_name)
            if record:
                record.metadata.update(metadata.to_dict())

        logger.info("Updated metadata for project '%s'.", project_name)
        self._publish_event("metadata.updated", {"project_name": project_name, "metadata": metadata.to_dict()})

    def extract_metadata_from_project(self, project_path: Union[str, Path]) -> ProjectMetadata:
        """Auto-extract operational metadata from project directory files."""
        path = Path(project_path).resolve()
        metadata = ProjectMetadata()

        if not path.exists() or not path.is_dir():
            return metadata

        # Extract from genova_project.json
        marker1 = path / "genova_project.json"
        marker2 = path / ".genova" / "project.json"
        m_file = marker1 if marker1.is_file() else (marker2 if marker2.is_file() else None)

        if m_file:
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    metadata.purpose = data.get("purpose", data.get("description", ""))
                    metadata.primary_technologies = data.get("technologies", data.get("primary_technologies", []))
                    metadata.supported_operations = data.get("operations", data.get("supported_operations", []))
                    metadata.entry_points = data.get("entry_points", {})
                    metadata.maintainers = data.get("maintainers", [])
                    metadata.tags = data.get("tags", [])
                    metadata.custom_attributes = data.get("custom_attributes", {})
            except Exception:
                pass

        # Infer default operations if empty
        if not metadata.supported_operations:
            ops = ["inspect", "health_check"]
            if (path / "main.py").is_file() or (path / "train.py").is_file() or (path / "app.py").is_file():
                ops.append("execute")
            if (path / "tests").is_dir():
                ops.append("test")
            metadata.supported_operations = ops

        # Infer primary technologies
        if not metadata.primary_technologies:
            techs = ["Python"]
            req_file = path / "requirements.txt"
            if req_file.is_file():
                try:
                    text = req_file.read_text(encoding="utf-8").lower()
                    if "torch" in text:
                        techs.append("PyTorch")
                    if "tensorflow" in text:
                        techs.append("TensorFlow")
                    if "pandas" in text:
                        techs.append("Pandas")
                    if "fastapi" in text:
                        techs.append("FastAPI")
                    if "flask" in text:
                        techs.append("Flask")
                except Exception:
                    pass
            metadata.primary_technologies = techs

        return metadata

    def list_supported_operations(self, project_name: str) -> List[str]:
        """Return list of supported operational actions for a project."""
        meta = self.get_metadata(project_name)
        return meta.supported_operations

    def supports_operation(self, project_name: str, operation: str) -> bool:
        """Check if project supports a specific operation."""
        meta = self.get_metadata(project_name)
        return meta.supports_operation(operation)

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish event via EventBus if connected."""
        if self._operator and hasattr(self._operator, "event_bus"):
            self._operator.event_bus.publish(
                OperatorEvent(
                    event_type=event_type,
                    payload=payload,
                    source=self.name,
                )
            )
