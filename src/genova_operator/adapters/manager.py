"""ProjectAdapterRegistry component for Genova Operator.

Manages, auto-detects, and dispatches operational actions to project domain adapters.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.adapters.base import BaseProjectAdapter
from genova_operator.adapters.clarify import ClarifyAdapter
from genova_operator.adapters.genefusionai import GeneFusionAIAdapter
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus

logger = logging.getLogger(__name__)


class ProjectAdapterRegistry(BaseComponent):
    """Central manager for registering, matching, and executing project adapters."""

    def __init__(
        self,
        name: str = "project-adapters",
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED
        self._adapters: Dict[str, BaseProjectAdapter] = {}

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize adapter registry and load default domain adapters."""
        logger.info("Initializing ProjectAdapterRegistry (%s)...", self._name)
        # Register built-in adapters
        self.register_adapter(GeneFusionAIAdapter())
        self.register_adapter(ClarifyAdapter())
        self._status = OperatorStatus.READY
        logger.info("ProjectAdapterRegistry initialized with %d adapters.", len(self._adapters))

    def shutdown(self) -> None:
        """Shutdown ProjectAdapterRegistry."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def register_adapter(self, adapter: BaseProjectAdapter) -> None:
        """Register a domain project adapter."""
        self._adapters[adapter.name] = adapter
        logger.info("Registered project adapter '%s' (%s).", adapter.name, adapter.adapter_type)

    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._adapters.keys())

    def get_adapter(self, adapter_name: str) -> Optional[BaseProjectAdapter]:
        """Get registered adapter by name."""
        return self._adapters.get(adapter_name)

    def find_adapter_for_project(self, project_path: Union[str, Path]) -> Optional[BaseProjectAdapter]:
        """Find matching adapter for a project path."""
        path = Path(project_path).resolve()
        for adapter in self._adapters.values():
            if adapter.is_applicable(path):
                return adapter
        return None

    def inspect_project_adapter(self, project_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Run adapter inspection if a matching adapter exists for the project."""
        adapter = self.find_adapter_for_project(project_path)
        if adapter:
            return adapter.inspect_adapter_status(project_path)
        return None

    def execute_action(
        self,
        project_path: Union[str, Path],
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute action via matching adapter for a project."""
        adapter = self.find_adapter_for_project(project_path)
        if not adapter:
            raise ValueError(f"No applicable adapter found for project path '{project_path}'.")
        return adapter.execute_action(action_name=action_name, project_path=project_path, params=params)
