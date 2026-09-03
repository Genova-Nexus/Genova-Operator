"""Exception hierarchy for Genova Operator."""

from typing import Any, Dict, Optional


class GenovaOperatorError(Exception):
    """Base exception class for all errors raised by Genova Operator."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ComponentInitializationError(GenovaOperatorError):
    """Raised when a core subsystem or component fails to initialize."""
    pass


class TaskExecutionError(GenovaOperatorError):
    """Raised when task execution fails or encounters an unrecoverable error."""
    pass


class ProjectNotFoundError(GenovaOperatorError):
    """Raised when a requested project cannot be located in the workspace or registry."""
    pass


class ConfigurationError(GenovaOperatorError):
    """Raised when configuration validation fails or a setting is missing/invalid."""
    pass


class ComponentNotFoundError(GenovaOperatorError):
    """Raised when requesting a sub-component that has not been registered."""
    pass
