"""Core interfaces and component protocols for Genova Operator.

Establishes standard structural boundaries for sub-components (Config, Registry,
Execution Engine, Monitoring, Automation, etc.) added across the 60-Day roadmap.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from genova_operator.core.types import OperatorStatus, TaskRequest, TaskResult


class BaseComponent(ABC):
    """Abstract base class for all Genova Operator sub-components."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique component identifier name."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize component resources."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up component resources."""
        pass

    @abstractmethod
    def get_status(self) -> OperatorStatus:
        """Retrieve current component status."""
        pass


class BaseTaskRunner(ABC):
    """Abstract interface for task execution engines."""

    @abstractmethod
    def execute_task(self, request: TaskRequest) -> TaskResult:
        """Execute a task request synchronously and return a TaskResult."""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Attempt to cancel an active task by task ID."""
        pass


class BaseProjectRegistry(ABC):
    """Abstract interface for Genova project discovery & registration."""

    @abstractmethod
    def register_project(self, name: str, path: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """Register a new project in the workspace."""
        pass

    @abstractmethod
    def get_project(self, name: str) -> Optional[Any]:
        """Retrieve project metadata by project name."""
        pass

    @abstractmethod
    def list_projects(self) -> Dict[str, Any]:
        """List all registered projects."""
        pass
