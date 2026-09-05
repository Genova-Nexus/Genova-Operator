"""ConfigManager component for Genova Operator.

Manages loading, merging, validating, and persisting configuration settings.
Supports loading from default objects, dictionaries, JSON files, and environment variables.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from genova_operator.config.models import (
    AutomationConfig,
    ExecutionConfig,
    MonitoringConfig,
    OperatorConfig,
    ProjectConfig,
    WorkspaceConfig,
)
from genova_operator.config.validator import validate_config
from genova_operator.core.exceptions import ConfigurationError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.types import OperatorEvent, OperatorStatus

logger = logging.getLogger(__name__)


class ConfigManager(BaseComponent):
    """Configuration Manager component for Genova Operator.

    Integrates into GenovaOperator core as a BaseComponent.
    Handles configuration loading, environment overrides, project isolation,
    and event notification.
    """

    def __init__(self, config: Optional[OperatorConfig] = None, name: str = "operator-config") -> None:
        self._name = name
        self._config = config or OperatorConfig()
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> OperatorConfig:
        return self._config

    def initialize(self) -> None:
        """Initialize the configuration manager, applying environment overrides and validation."""
        logger.info("Initializing ConfigManager (%s)...", self._name)
        try:
            self.load_from_env()
            validate_config(self._config)
            self._status = OperatorStatus.READY
            logger.info("ConfigManager initialized successfully.")
        except Exception as err:
            self._status = OperatorStatus.ERROR
            raise ConfigurationError(f"Failed to initialize ConfigManager: {err}") from err

    def shutdown(self) -> None:
        """Shutdown ConfigManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def load_from_dict(self, data: Dict[str, Any], validate: bool = True) -> None:
        """Load and merge configuration settings from a dictionary."""
        new_config = OperatorConfig.from_dict(data)
        self._merge_config(new_config)
        if validate:
            validate_config(self._config)

    def load_from_file(self, file_path: Union[str, Path], validate: bool = True) -> None:
        """Load configuration settings from a JSON configuration file."""
        path = Path(file_path)
        if not path.is_file():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.load_from_dict(data, validate=validate)
        except json.JSONDecodeError as err:
            raise ConfigurationError(f"Invalid JSON format in config file '{path}': {err}") from err
        except Exception as err:
            raise ConfigurationError(f"Error reading config file '{path}': {err}") from err

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save the current configuration state to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2)
        except Exception as err:
            raise ConfigurationError(f"Error saving config file '{path}': {err}") from err

    def load_from_env(self, prefix: str = "GENOVA_OPERATOR_") -> None:
        """Parse environment variables matching prefix and apply overrides.

        Examples:
            GENOVA_OPERATOR_WORKSPACE_ROOT_PATH -> config.workspace.root_path
            GENOVA_OPERATOR_EXECUTION_DEFAULT_TIMEOUT -> config.execution.default_timeout
            GENOVA_OPERATOR_MONITORING_POLLING_INTERVAL -> config.monitoring.polling_interval
        """
        for env_key, env_val in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            sub_key = env_key[len(prefix):].lower()

            if sub_key == "workspace_root_path":
                self._config.workspace.root_path = env_val
            elif sub_key == "workspace_projects_dir":
                self._config.workspace.projects_dir = env_val
            elif sub_key == "execution_default_timeout":
                try:
                    self._config.execution.default_timeout = float(env_val)
                except ValueError:
                    pass
            elif sub_key == "execution_max_concurrent_tasks":
                try:
                    self._config.execution.max_concurrent_tasks = int(env_val)
                except ValueError:
                    pass
            elif sub_key == "monitoring_polling_interval":
                try:
                    self._config.monitoring.polling_interval = float(env_val)
                except ValueError:
                    pass
            elif sub_key == "automation_enable_scheduler":
                self._config.automation.enable_scheduler = env_val.lower() in ("true", "1", "yes")

    def get_project_config(self, name: str) -> Optional[ProjectConfig]:
        """Retrieve ProjectConfig for a specific project (e.g. GeneFusionAI or Clarify)."""
        return self._config.get_project(name)

    def set_project_config(self, project: ProjectConfig, validate: bool = True) -> None:
        """Add or update a ProjectConfig."""
        self._config.set_project(project)
        if validate:
            validate_config(self._config)

    def _merge_config(self, new_config: OperatorConfig) -> None:
        """Merge new_config into existing config."""
        self._config.workspace = new_config.workspace
        self._config.execution = new_config.execution
        self._config.monitoring = new_config.monitoring
        self._config.automation = new_config.automation
        for p_name, p_config in new_config.projects.items():
            self._config.projects[p_name] = p_config
