"""Project State models for Genova Operator.

Defines ProjectState enums, StateTransitionRecord, and ProjectStateSummary objects
used to track project lifecycle states and connect them with running tasks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProjectState(Enum):
    """Lifecycle and operational state of a registered project."""
    AVAILABLE = "AVAILABLE"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RUNNING = "RUNNING"
    UNHEALTHY = "UNHEALTHY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class StateTransitionRecord:
    """Audit record capturing a project state transition event.

    Attributes:
        project_name: Name of the project.
        previous_state: Previous ProjectState.
        new_state: New ProjectState.
        reason: Optional description or trigger for the transition.
        task_id: Optional associated active task ID.
        timestamp: Epoch timestamp when transition occurred.
    """
    project_name: str
    previous_state: ProjectState
    new_state: ProjectState
    reason: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "previous_state": self.previous_state.value,
            "new_state": self.new_state.value,
            "reason": self.reason,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
        }


@dataclass
class ProjectStateSummary:
    """Summary of current state and historical transitions for a project.

    Attributes:
        project_name: Name of the project.
        current_state: Current ProjectState.
        active_tasks: List of currently running task IDs.
        last_transition: Epoch timestamp of latest state change.
        history: List of StateTransitionRecord objects.
    """
    project_name: str
    current_state: ProjectState = ProjectState.AVAILABLE
    active_tasks: List[str] = field(default_factory=list)
    last_transition: float = field(default_factory=time.time)
    history: List[StateTransitionRecord] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        """Return True if project state is RUNNING or has active tasks."""
        return self.current_state == ProjectState.RUNNING or len(self.active_tasks) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "current_state": self.current_state.value,
            "active_tasks": self.active_tasks,
            "is_running": self.is_running,
            "last_transition": self.last_transition,
            "history_count": len(self.history),
            "history": [h.to_dict() for h in self.history],
        }
