"""Project Registry models for Genova Operator.

Defines project identity, repository information, environment information, and the
comprehensive ProjectRecord model representing registered projects (such as GeneFusionAI and Clarify).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectIdentity:
    """Project identification details.

    Attributes:
        name: Short unique identifier name of the project (e.g., 'GeneFusionAI', 'Clarify').
        display_name: Human-readable project title.
        description: Description of the project's purpose.
        project_type: Type/category of project (e.g. 'python_library', 'ml_research', 'web_application').
        project_id: Unique identifier UUID string.
    """
    name: str
    display_name: Optional[str] = None
    description: str = ""
    project_type: str = "python"
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name or self.name,
            "description": self.description,
            "project_type": self.project_type,
            "project_id": self.project_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectIdentity:
        return cls(
            name=data["name"],
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            project_type=data.get("project_type", "python"),
            project_id=data.get("project_id", str(uuid.uuid4())),
        )


@dataclass
class RepositoryInfo:
    """Git repository metadata for a project.

    Attributes:
        remote_url: Remote Git repository URL.
        branch: Current/default Git branch.
        commit_hash: Current commit revision SHA hash.
        is_dirty: True if repository has uncommitted changes.
    """
    remote_url: Optional[str] = None
    branch: str = "main"
    commit_hash: Optional[str] = None
    is_dirty: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "remote_url": self.remote_url,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "is_dirty": self.is_dirty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RepositoryInfo:
        return cls(
            remote_url=data.get("remote_url"),
            branch=data.get("branch", "main"),
            commit_hash=data.get("commit_hash"),
            is_dirty=bool(data.get("is_dirty", False)),
        )


@dataclass
class EnvironmentInfo:
    """Runtime and dependency environment details for a project.

    Attributes:
        environment_type: Environment category ('venv', 'conda', 'system', 'docker').
        python_interpreter: Path to the Python executable.
        env_vars: Environment variables required by the project.
        dependencies: List of primary project dependencies or requirements files.
    """
    environment_type: str = "system"
    python_interpreter: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment_type": self.environment_type,
            "python_interpreter": self.python_interpreter,
            "env_vars": self.env_vars,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnvironmentInfo:
        return cls(
            environment_type=data.get("environment_type", "system"),
            python_interpreter=data.get("python_interpreter"),
            env_vars=dict(data.get("env_vars", {})),
            dependencies=list(data.get("dependencies", [])),
        )


@dataclass
class ProjectRecord:
    """Complete source of truth record for a registered Genova project.

    Combines project identity, filesystem location, repository information,
    environment info, available entry points, commands, and operational configuration.
    """
    identity: ProjectIdentity
    path: str = "."
    repository: RepositoryInfo = field(default_factory=RepositoryInfo)
    environment: EnvironmentInfo = field(default_factory=EnvironmentInfo)
    entry_points: Dict[str, str] = field(default_factory=dict)
    available_commands: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)

    @property
    def name(self) -> str:
        return self.identity.name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "path": self.path,
            "repository": self.repository.to_dict(),
            "environment": self.environment.to_dict(),
            "entry_points": self.entry_points,
            "available_commands": self.available_commands,
            "options": self.options,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
            "last_active_at": self.last_active_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectRecord:
        identity_data = data["identity"] if "identity" in data else {"name": data["name"]}
        return cls(
            identity=ProjectIdentity.from_dict(identity_data),
            path=str(data.get("path", ".")),
            repository=RepositoryInfo.from_dict(data.get("repository", {})),
            environment=EnvironmentInfo.from_dict(data.get("environment", {})),
            entry_points=dict(data.get("entry_points", {})),
            available_commands=list(data.get("available_commands", [])),
            options=dict(data.get("options", {})),
            metadata=dict(data.get("metadata", {})),
            registered_at=float(data.get("registered_at", time.time())),
            last_active_at=float(data.get("last_active_at", time.time())),
        )
