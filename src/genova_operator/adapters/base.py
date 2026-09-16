"""Base Project Adapter interface for Genova Operator.

Defines the abstract interface for project-specific domain adapters like GeneFusionAI and Clarify.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class BaseProjectAdapter(ABC):
    """Abstract base class for project domain adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the adapter."""
        pass

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Domain type identifier (e.g. 'genomics', 'clinical_nlp')."""
        pass

    @abstractmethod
    def is_applicable(self, project_path: Union[str, Path]) -> bool:
        """Check whether this adapter applies to a given project path.

        Args:
            project_path: Path to target project directory.

        Returns:
            True if adapter applies to project.
        """
        pass

    @abstractmethod
    def inspect_adapter_status(self, project_path: Union[str, Path]) -> Dict[str, Any]:
        """Perform adapter-specific domain readiness inspection.

        Args:
            project_path: Target project path.

        Returns:
            Status dictionary containing readiness flags and details.
        """
        pass

    @abstractmethod
    def list_supported_actions(self) -> List[str]:
        """List supported domain action names."""
        pass

    @abstractmethod
    def execute_action(
        self,
        action_name: str,
        project_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a domain action.

        Args:
            action_name: Name of action to execute.
            project_path: Target project directory path.
            params: Optional execution parameters.

        Returns:
            Result dictionary.
        """
        pass
