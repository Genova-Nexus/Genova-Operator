"""ProjectStateManager component for Genova Operator.

Manages thread-safe state transitions, active task coupling, health synchronization,
and state change event broadcasting.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from genova_operator.core.exceptions import GenovaOperatorError, ProjectNotFoundError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.health.manager import ProjectHealthManager
from genova_operator.health.models import HealthStatus, ProjectHealthReport
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.state.models import (
    ProjectState,
    ProjectStateSummary,
    StateTransitionRecord,
)

logger = logging.getLogger(__name__)


class ProjectStateManager(BaseComponent):
    """Project State Manager component for Genova Operator.

    Tracks and updates operational project states (AVAILABLE, ACTIVE, INACTIVE, RUNNING, UNHEALTHY, UNAVAILABLE).
    """

    def __init__(
        self,
        name: str = "project-state",
        project_registry: Optional[ProjectRegistry] = None,
        project_health_manager: Optional[ProjectHealthManager] = None,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._project_registry = project_registry
        self._health_manager = project_health_manager
        self._operator = operator
        self._lock = threading.RLock()
        self._status = OperatorStatus.UNINITIALIZED
        self._summaries: Dict[str, ProjectStateSummary] = {}

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize ProjectStateManager."""
        logger.info("Initializing ProjectStateManager (%s)...", self._name)
        with self._lock:
            if self._project_registry:
                for proj_name in self._project_registry.list_projects():
                    if proj_name not in self._summaries:
                        self._summaries[proj_name] = ProjectStateSummary(
                            project_name=proj_name,
                            current_state=ProjectState.AVAILABLE,
                        )

            self._status = OperatorStatus.READY
            logger.info("ProjectStateManager initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectStateManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def get_project_state(self, project_name: str) -> ProjectState:
        """Get current ProjectState for a project name."""
        with self._lock:
            summary = self._get_or_create_summary(project_name)
            return summary.current_state

    def set_project_state(
        self,
        project_name: str,
        new_state: ProjectState,
        reason: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> StateTransitionRecord:
        """Transition project state and publish state change event over EventBus.

        Args:
            project_name: Target project name.
            new_state: New ProjectState enum value.
            reason: Optional reason string.
            task_id: Optional active task ID.

        Returns:
            StateTransitionRecord instance.
        """
        with self._lock:
            summary = self._get_or_create_summary(project_name)
            previous_state = summary.current_state

            if previous_state == new_state and not task_id:
                logger.debug("Project '%s' state unchanged (%s).", project_name, new_state.value)

            transition = StateTransitionRecord(
                project_name=project_name,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason,
                task_id=task_id,
                timestamp=time.time(),
            )

            summary.current_state = new_state
            summary.last_transition = transition.timestamp
            summary.history.append(transition)

            logger.info(
                "Project '%s' state changed: %s -> %s (Reason: %s).",
                project_name,
                previous_state.value,
                new_state.value,
                reason or "manual update",
            )

            self._publish_event("state.changed", transition.to_dict())
            return transition

    def associate_task(self, project_name: str, task_id: str) -> StateTransitionRecord:
        """Associate an active task ID with a project, transitioning state to RUNNING."""
        with self._lock:
            summary = self._get_or_create_summary(project_name)
            if task_id not in summary.active_tasks:
                summary.active_tasks.append(task_id)

            return self.set_project_state(
                project_name=project_name,
                new_state=ProjectState.RUNNING,
                reason=f"Task '{task_id}' started",
                task_id=task_id,
            )

    def disassociate_task(
        self,
        project_name: str,
        task_id: str,
        fallback_state: ProjectState = ProjectState.ACTIVE,
    ) -> StateTransitionRecord:
        """Disassociate a completed/cancelled task ID from a project."""
        with self._lock:
            summary = self._get_or_create_summary(project_name)
            if task_id in summary.active_tasks:
                summary.active_tasks.remove(task_id)

            next_state = ProjectState.RUNNING if len(summary.active_tasks) > 0 else fallback_state
            return self.set_project_state(
                project_name=project_name,
                new_state=next_state,
                reason=f"Task '{task_id}' finished",
                task_id=task_id,
            )

    def update_from_health(self, project_name: str, health_report: ProjectHealthReport) -> StateTransitionRecord:
        """Update project state based on a ProjectHealthReport."""
        with self._lock:
            summary = self._get_or_create_summary(project_name)

            if health_report.status == HealthStatus.UNAVAILABLE:
                target_state = ProjectState.UNAVAILABLE
            elif health_report.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
                target_state = ProjectState.UNHEALTHY
            elif summary.is_running:
                target_state = ProjectState.RUNNING
            else:
                target_state = ProjectState.AVAILABLE

            return self.set_project_state(
                project_name=project_name,
                new_state=target_state,
                reason=f"Health report status: {health_report.status.value}",
            )

    def get_state_summary(self, project_name: str) -> ProjectStateSummary:
        """Retrieve ProjectStateSummary for a project."""
        with self._lock:
            return self._get_or_create_summary(project_name)

    def list_states(self) -> Dict[str, ProjectState]:
        """List current states for all tracked projects."""
        with self._lock:
            return {name: s.current_state for name, s in self._summaries.items()}

    def _get_or_create_summary(self, project_name: str) -> ProjectStateSummary:
        """Internal helper to fetch or create a ProjectStateSummary."""
        if project_name not in self._summaries:
            self._summaries[project_name] = ProjectStateSummary(
                project_name=project_name,
                current_state=ProjectState.AVAILABLE,
            )
        return self._summaries[project_name]

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish event via GenovaOperator EventBus if connected."""
        if self._operator and hasattr(self._operator, "event_bus"):
            self._operator.event_bus.publish(
                OperatorEvent(
                    event_type=event_type,
                    payload=payload,
                    source=self.name,
                )
            )
