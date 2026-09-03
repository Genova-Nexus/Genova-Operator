"""Central Orchestrator class for Genova Operator.

Acts as the primary entry point and component coordinator for the library.
Manages component lifecycle, event distribution, task submission, and operational state.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Type, TypeVar

from genova_operator.core.event_bus import EventBus
from genova_operator.core.exceptions import (
    ComponentInitializationError,
    ComponentNotFoundError,
    TaskExecutionError,
)
from genova_operator.core.interfaces import BaseComponent, BaseTaskRunner
from genova_operator.core.types import (
    OperatorEvent,
    OperatorStatus,
    TaskRequest,
    TaskResult,
    TaskState,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseComponent)


class GenovaOperator:
    """Central orchestrator for Genova Operator.

    "Genova Nexus thinks, Genova Operator acts."

    Attributes:
        event_bus: Thread-safe EventBus instance.
    """

    def __init__(self, name: str = "genova-operator-core") -> None:
        self.name = name
        self.event_bus = EventBus()
        self._components: Dict[str, BaseComponent] = {}
        self._status = OperatorStatus.UNINITIALIZED
        self._runner: Optional[BaseTaskRunner] = None

    @property
    def status(self) -> OperatorStatus:
        """Return current status of GenovaOperator."""
        return self._status

    def initialize(self) -> None:
        """Initialize the core operator and all registered components."""
        logger.info("Initializing GenovaOperator core (%s)...", self.name)
        try:
            for component_name, component in self._components.items():
                logger.debug("Initializing sub-component: %s", component_name)
                component.initialize()

            self._status = OperatorStatus.READY
            self.event_bus.publish(
                OperatorEvent(
                    event_type="operator.initialized",
                    payload={"status": self._status.value, "components": list(self._components.keys())},
                    source=self.name,
                )
            )
            logger.info("GenovaOperator initialized successfully.")
        except Exception as err:
            self._status = OperatorStatus.ERROR
            logger.error("Failed to initialize GenovaOperator: %s", err)
            raise ComponentInitializationError(
                f"Core operator initialization failed: {err}"
            ) from err

    def register_component(self, component: BaseComponent) -> None:
        """Register a sub-component with the core orchestrator.

        Args:
            component: Instance of BaseComponent.
        """
        if component.name in self._components:
            logger.warning("Overwriting existing registered component: %s", component.name)
        self._components[component.name] = component
        logger.info("Registered component: %s", component.name)

        if isinstance(component, BaseTaskRunner):
            self._runner = component

        if self._status == OperatorStatus.READY:
            component.initialize()

    def get_component(self, name: str) -> BaseComponent:
        """Retrieve a registered sub-component by name.

        Args:
            name: Component identifier name.

        Returns:
            The registered BaseComponent instance.

        Raises:
            ComponentNotFoundError: If component is not registered.
        """
        if name not in self._components:
            raise ComponentNotFoundError(f"Component '{name}' is not registered.")
        return self._components[name]

    def has_component(self, name: str) -> bool:
        """Check if a component is registered."""
        return name in self._components

    def submit_task(self, request: TaskRequest) -> TaskResult:
        """Submit a task request to Genova Operator for execution.

        Args:
            request: Standard TaskRequest object.

        Returns:
            Standard TaskResult object.

        Raises:
            TaskExecutionError: If operator is not initialized or task fails execution.
        """
        if self._status != OperatorStatus.READY:
            raise TaskExecutionError(
                f"Cannot submit task. Operator status is '{self._status.value}' (must be 'READY')."
            )

        start_time = time.time()
        self.event_bus.publish(
            OperatorEvent(
                event_type="task.submitted",
                payload={"task_id": request.task_id, "action": request.action},
                source=self.name,
            )
        )

        if self._runner is not None:
            return self._runner.execute_task(request)

        # Default fallback execution handler when no custom runner registered
        duration = time.time() - start_time
        result = TaskResult(
            task_id=request.task_id,
            status=TaskState.COMPLETED,
            action=request.action,
            project_name=request.project_name,
            exit_code=0,
            stdout=f"Action '{request.action}' acknowledged by core operator.",
            duration=duration,
            metadata={"handler": "default_core"},
        )

        self.event_bus.publish(
            OperatorEvent(
                event_type="task.completed",
                payload={"task_id": result.task_id, "status": result.status.value},
                source=self.name,
            )
        )
        return result

    def get_status_report(self) -> Dict[str, Any]:
        """Generate a complete operational status report of the operator and components."""
        component_statuses = {}
        for name, comp in self._components.items():
            try:
                component_statuses[name] = comp.get_status().value
            except Exception as err:
                component_statuses[name] = f"ERROR: {err}"

        return {
            "name": self.name,
            "status": self._status.value,
            "components_count": len(self._components),
            "components": component_statuses,
            "has_runner": self._runner is not None,
        }

    def shutdown(self) -> None:
        """Shutdown the operator and clean up all registered components."""
        logger.info("Shutting down GenovaOperator...")
        for name, comp in self._components.items():
            try:
                comp.shutdown()
            except Exception as err:
                logger.error("Error shutting down component '%s': %s", name, err)

        self._status = OperatorStatus.SHUTDOWN
        self.event_bus.publish(
            OperatorEvent(
                event_type="operator.shutdown",
                payload={"status": self._status.value},
                source=self.name,
            )
        )
        logger.info("GenovaOperator shutdown complete.")
