"""Core data contracts and types for Genova Operator.

Defines standard task requests, task results, states, status enums, and event objects
used throughout the Genova Operator library and its communication with Genova Nexus.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional


class TaskState(Enum):
    """Execution state of a task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class OperatorStatus(Enum):
    """Overall operational status of Genova Operator or its components."""
    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    BUSY = "BUSY"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class TaskRequest:
    """Standardized task request submitted to Genova Operator.

    Attributes:
        action: The name of the operational action to perform.
        project_name: Optional target project name (e.g. 'GeneFusionAI', 'Clarify').
        parameters: Dictionary of parameters passed to the action.
        task_id: Unique task identifier (auto-generated if omitted).
        options: Execution configuration options (e.g., timeout, env vars).
        metadata: Arbitrary operational metadata associated with the request.
        created_at: Epoch timestamp when request was created.
    """
    action: str
    project_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    options: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskRequest to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "action": self.action,
            "project_name": self.project_name,
            "parameters": self.parameters,
            "options": self.options,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskRequest:
        """Create a TaskRequest instance from a dictionary."""
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            action=data["action"],
            project_name=data.get("project_name"),
            parameters=data.get("parameters", {}),
            options=data.get("options", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
        )


@dataclass
class TaskResult:
    """Standardized operational result returned by Genova Operator.

    Attributes:
        task_id: Unique identifier matching the TaskRequest.
        status: Final or current TaskState.
        action: Action name executed.
        project_name: Target project name.
        exit_code: Execution exit code (0 for success, non-zero for failure).
        stdout: Standard output captured.
        stderr: Standard error captured.
        result_data: Output data dictionary or artifacts.
        error_message: Optional error message if status is FAILED.
        duration: Execution time in seconds.
        metadata: Additional task metadata.
        completed_at: Epoch timestamp when task finished.
    """
    task_id: str
    status: TaskState
    action: str
    project_name: Optional[str] = None
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: float = field(default_factory=time.time)

    @property
    def is_success(self) -> bool:
        """Return True if task completed successfully with exit_code 0."""
        return self.status == TaskState.COMPLETED and self.exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskResult to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "action": self.action,
            "project_name": self.project_name,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "duration": self.duration,
            "metadata": self.metadata,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskResult:
        """Create a TaskResult instance from a dictionary."""
        return cls(
            task_id=data["task_id"],
            status=TaskState(data["status"]),
            action=data["action"],
            project_name=data.get("project_name"),
            exit_code=data.get("exit_code", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            result_data=data.get("result_data", {}),
            error_message=data.get("error_message"),
            duration=data.get("duration", 0.0),
            metadata=data.get("metadata", {}),
            completed_at=data.get("completed_at", time.time()),
        )


@dataclass
class OperatorEvent:
    """Event object dispatched over the EventBus.

    Attributes:
        event_type: Category or name of the event.
        payload: Event data dictionary.
        event_id: Unique event identifier.
        source: Component or module that emitted the event.
        timestamp: Epoch timestamp when event was created.
    """
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "core"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OperatorEvent to a dictionary representation."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
