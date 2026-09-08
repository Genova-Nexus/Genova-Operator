"""Project Discovery models for Genova Operator.

Defines project confidence enums and DiscoveredProject models used during
automatic project detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from genova_operator.registry.models import (
    EnvironmentInfo,
    ProjectIdentity,
    ProjectRecord,
    RepositoryInfo,
)


class ProjectConfidence(Enum):
    """Confidence level of project detection."""
    NOT_A_PROJECT = "NOT_A_PROJECT"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @property
    def score(self) -> float:
        """Numeric score representation of confidence."""
        scores = {
            ProjectConfidence.NOT_A_PROJECT: 0.0,
            ProjectConfidence.LOW: 0.3,
            ProjectConfidence.MEDIUM: 0.6,
            ProjectConfidence.HIGH: 1.0,
        }
        return scores[self]


@dataclass
class DiscoveredProject:
    """Represents a project detected during workspace discovery.

    Attributes:
        name: Inferred or detected project name.
        path: Path string to project root.
        confidence: Detection ProjectConfidence enum.
        project_type: Detected project category (e.g. 'python_library', 'ml_research').
        matched_rules: List of detection rules/markers that matched.
        detected_entry_points: Inferred entry points (e.g. scripts/train.py).
        python_interpreter: Suggested Python interpreter path if found.
        env_type: Suggested environment type ('venv', 'conda', 'system').
        metadata: Additional discovery metadata.
    """
    name: str
    path: str
    confidence: ProjectConfidence = ProjectConfidence.MEDIUM
    project_type: str = "python"
    matched_rules: List[str] = field(default_factory=list)
    detected_entry_points: Dict[str, str] = field(default_factory=dict)
    python_interpreter: Optional[str] = None
    env_type: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_project_record(self) -> ProjectRecord:
        """Convert DiscoveredProject into a ProjectRecord for ProjectRegistry."""
        identity = ProjectIdentity(
            name=self.name,
            display_name=self.name,
            project_type=self.project_type,
        )
        repo_info = RepositoryInfo(
            remote_url=self.metadata.get("git_remote"),
            branch=self.metadata.get("git_branch", "main"),
        )
        env_info = EnvironmentInfo(
            environment_type=self.env_type,
            python_interpreter=self.python_interpreter,
            dependencies=self.metadata.get("dependencies", []),
        )
        return ProjectRecord(
            identity=identity,
            path=self.path,
            repository=repo_info,
            environment=env_info,
            entry_points=self.detected_entry_points,
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "confidence": self.confidence.value,
            "score": self.confidence.score,
            "project_type": self.project_type,
            "matched_rules": self.matched_rules,
            "detected_entry_points": self.detected_entry_points,
            "python_interpreter": self.python_interpreter,
            "env_type": self.env_type,
            "metadata": self.metadata,
        }
