"""Configuration validation logic for Genova Operator.

Ensures configuration fields adhere to required types, ranges, non-negative values,
and valid formatting.
"""

from __future__ import annotations

from typing import Any, Dict

from genova_operator.config.models import OperatorConfig
from genova_operator.core.exceptions import ConfigurationError


def validate_config(config: OperatorConfig) -> None:
    """Validate an OperatorConfig instance.

    Args:
        config: The OperatorConfig to validate.

    Raises:
        ConfigurationError: If any configuration value is invalid.
    """
    # Validate Execution Config
    if config.execution.default_timeout < 0:
        raise ConfigurationError("execution.default_timeout must be non-negative (>= 0).")
    if config.execution.max_concurrent_tasks <= 0:
        raise ConfigurationError("execution.max_concurrent_tasks must be greater than 0.")

    # Validate Monitoring Config
    if config.monitoring.polling_interval <= 0:
        raise ConfigurationError("monitoring.polling_interval must be greater than 0.")
    if config.monitoring.log_retention_days < 0:
        raise ConfigurationError("monitoring.log_retention_days must be non-negative.")
    if config.monitoring.max_log_file_mb <= 0:
        raise ConfigurationError("monitoring.max_log_file_mb must be greater than 0.")

    # Validate Automation Config
    if config.automation.max_retry_attempts < 0:
        raise ConfigurationError("automation.max_retry_attempts must be non-negative.")
    if config.automation.retry_delay_seconds < 0:
        raise ConfigurationError("automation.retry_delay_seconds must be non-negative.")

    # Validate Projects
    for project_name, proj in config.projects.items():
        if not proj.name:
            raise ConfigurationError(f"Project configuration under key '{project_name}' has an empty name.")
        if not proj.path:
            raise ConfigurationError(f"Project '{proj.name}' has an empty root path.")
