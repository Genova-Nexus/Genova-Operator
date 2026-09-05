"""Configuration data models for Genova Operator.

Defines workspace, execution, monitoring, automation, and project-specific
configuration models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class WorkspaceConfig:
    """Configuration settings for the Genova workspace environment.

    Attributes:
        root_path: Root directory path of the workspace.
        projects_dir: Directory where projects are located relative to root.
        auto_discovery: Whether automatic project discovery is enabled.
    """
    root_path: str = "."
    projects_dir: str = "projects"
    auto_discovery: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_path": self.root_path,
            "projects_dir": self.projects_dir,
            "auto_discovery": self.auto_discovery,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkspaceConfig:
        return cls(
            root_path=str(data.get("root_path", ".")),
            projects_dir=str(data.get("projects_dir", "projects")),
            auto_discovery=bool(data.get("auto_discovery", True)),
        )


@dataclass
class ExecutionConfig:
    """Execution settings and defaults for command and task execution.

    Attributes:
        default_timeout: Default task timeout in seconds (0 = no timeout).
        max_concurrent_tasks: Maximum parallel background tasks allowed.
        default_shell: Default shell executable to use.
        working_directory: Default base working directory.
    """
    default_timeout: float = 300.0
    max_concurrent_tasks: int = 5
    default_shell: Optional[str] = None
    working_directory: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_timeout": self.default_timeout,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "default_shell": self.default_shell,
            "working_directory": self.working_directory,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionConfig:
        return cls(
            default_timeout=float(data.get("default_timeout", 300.0)),
            max_concurrent_tasks=int(data.get("max_concurrent_tasks", 5)),
            default_shell=data.get("default_shell"),
            working_directory=data.get("working_directory"),
        )


@dataclass
class MonitoringConfig:
    """Monitoring and observability settings.

    Attributes:
        polling_interval: Resource polling frequency in seconds.
        enable_gpu_monitoring: Flag to enable GPU monitoring if hardware is available.
        log_retention_days: Number of days to retain task logs.
        max_log_file_mb: Maximum log size per task in megabytes.
    """
    polling_interval: float = 5.0
    enable_gpu_monitoring: bool = True
    log_retention_days: int = 30
    max_log_file_mb: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "polling_interval": self.polling_interval,
            "enable_gpu_monitoring": self.enable_gpu_monitoring,
            "log_retention_days": self.log_retention_days,
            "max_log_file_mb": self.max_log_file_mb,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MonitoringConfig:
        return cls(
            polling_interval=float(data.get("polling_interval", 5.0)),
            enable_gpu_monitoring=bool(data.get("enable_gpu_monitoring", True)),
            log_retention_days=int(data.get("log_retention_days", 30)),
            max_log_file_mb=int(data.get("max_log_file_mb", 50)),
        )


@dataclass
class AutomationConfig:
    """Automation, scheduling, and job execution settings.

    Attributes:
        enable_scheduler: Flag to enable background automated scheduler.
        max_retry_attempts: Maximum retry attempts for recoverable failures.
        retry_delay_seconds: Delay between automated retries in seconds.
    """
    enable_scheduler: bool = True
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 10.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_scheduler": self.enable_scheduler,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AutomationConfig:
        return cls(
            enable_scheduler=bool(data.get("enable_scheduler", True)),
            max_retry_attempts=int(data.get("max_retry_attempts", 3)),
            retry_delay_seconds=float(data.get("retry_delay_seconds", 10.0)),
        )


@dataclass
class ProjectConfig:
    """Project-specific operational configuration settings.

    Allows projects like GeneFusionAI and Clarify to hold independent settings
    while being managed through the central GenovaOperator.

    Attributes:
        name: Name of the project (e.g., 'GeneFusionAI', 'Clarify').
        path: Root directory path of the project.
        environment_type: Runtime environment type ('venv', 'conda', 'system', etc.).
        python_interpreter: Path to Python interpreter for this project.
        env_vars: Custom environment variables for project execution.
        options: Project-specific operational options and parameters.
    """
    name: str
    path: str = "."
    environment_type: str = "system"
    python_interpreter: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "environment_type": self.environment_type,
            "python_interpreter": self.python_interpreter,
            "env_vars": self.env_vars,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectConfig:
        return cls(
            name=data["name"],
            path=str(data.get("path", ".")),
            environment_type=str(data.get("environment_type", "system")),
            python_interpreter=data.get("python_interpreter"),
            env_vars=dict(data.get("env_vars", {})),
            options=dict(data.get("options", {})),
        )


@dataclass
class OperatorConfig:
    """Top-level configuration object for Genova Operator.

    Combines workspace, execution, monitoring, automation, and project-specific
    configurations into a unified structure.
    """
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    projects: Dict[str, ProjectConfig] = field(default_factory=dict)

    def get_project(self, name: str) -> Optional[ProjectConfig]:
        """Retrieve ProjectConfig by project name."""
        return self.projects.get(name)

    def set_project(self, project: ProjectConfig) -> None:
        """Register or update a ProjectConfig."""
        self.projects[project.name] = project

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace.to_dict(),
            "execution": self.execution.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "automation": self.automation.to_dict(),
            "projects": {name: p.to_dict() for name, p in self.projects.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OperatorConfig:
        projects_dict = {}
        if "projects" in data and isinstance(data["projects"], dict):
            for p_name, p_data in data["projects"].items():
                if isinstance(p_data, dict):
                    if "name" not in p_data:
                        p_data["name"] = p_name
                    projects_dict[p_name] = ProjectConfig.from_dict(p_data)

        return cls(
            workspace=WorkspaceConfig.from_dict(data.get("workspace", {})),
            execution=ExecutionConfig.from_dict(data.get("execution", {})),
            monitoring=MonitoringConfig.from_dict(data.get("monitoring", {})),
            automation=AutomationConfig.from_dict(data.get("automation", {})),
            projects=projects_dict,
        )
