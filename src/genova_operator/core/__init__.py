"""Genova Operator Core package.

Provides the foundational architecture, orchestrator, data contracts, and component
coordination for Genova Operator.
"""

from genova_operator.core.event_bus import EventBus
from genova_operator.core.exceptions import (
    ComponentInitializationError,
    ComponentNotFoundError,
    ConfigurationError,
    GenovaOperatorError,
    ProjectNotFoundError,
    TaskExecutionError,
)
from genova_operator.core.interfaces import (
    BaseComponent,
    BaseProjectRegistry,
    BaseTaskRunner,
)
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import (
    OperatorEvent,
    OperatorStatus,
    TaskRequest,
    TaskResult,
    TaskState,
)

__all__ = [
    "GenovaOperator",
    "EventBus",
    "TaskRequest",
    "TaskResult",
    "TaskState",
    "OperatorStatus",
    "OperatorEvent",
    "BaseComponent",
    "BaseTaskRunner",
    "BaseProjectRegistry",
    "GenovaOperatorError",
    "ComponentInitializationError",
    "TaskExecutionError",
    "ProjectNotFoundError",
    "ConfigurationError",
    "ComponentNotFoundError",
]
