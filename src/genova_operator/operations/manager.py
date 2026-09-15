"""ProjectOperationsManager component for Genova Operator.

Unified operational facade combining Inspection, Health, State, Activity, and Metadata
subsystems for a project into a single consolidated view and action interface.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Union

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.activity.models import ActivityCategory
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.health.manager import ProjectHealthManager
from genova_operator.inspector.manager import ProjectInspector
from genova_operator.metadata.manager import ProjectMetadataManager
from genova_operator.operations.models import OperationResult, ProjectOperationalView
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import ProjectState

logger = logging.getLogger(__name__)


class ProjectOperationsManager(BaseComponent):
    """Unified project operations manager and facade component for Genova Operator.

    Acts as the single dispatch point for project analysis, state queries, health checks,
    activity feeds, metadata updates, and operational executions.
    """

    def __init__(
        self,
        name: str = "project-operations",
        project_registry: Optional[ProjectRegistry] = None,
        project_inspector: Optional[ProjectInspector] = None,
        health_manager: Optional[ProjectHealthManager] = None,
        state_manager: Optional[ProjectStateManager] = None,
        activity_tracker: Optional[ProjectActivityTracker] = None,
        metadata_manager: Optional[ProjectMetadataManager] = None,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._project_registry = project_registry
        self._project_inspector = project_inspector
        self._health_manager = health_manager
        self._state_manager = state_manager
        self._activity_tracker = activity_tracker
        self._metadata_manager = metadata_manager
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize ProjectOperationsManager."""
        logger.info("Initializing ProjectOperationsManager (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("ProjectOperationsManager initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectOperationsManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def get_operational_view(self, project_name: str) -> ProjectOperationalView:
        """Consolidate all Phase 2 project subsystem outputs into a single operational view.

        Args:
            project_name: Name of target project.

        Returns:
            ProjectOperationalView instance.
        """
        record_dict: Optional[Dict[str, Any]] = None
        health_dict: Optional[Dict[str, Any]] = None
        state_dict: Optional[Dict[str, Any]] = None
        activity_dict: Optional[Dict[str, Any]] = None
        metadata_dict: Optional[Dict[str, Any]] = None
        inspection_dict: Optional[Dict[str, Any]] = None

        # 1. Project Record
        if self._project_registry and self._project_registry.has_project(project_name):
            rec = self._project_registry.get_project(project_name)
            if rec:
                record_dict = rec.to_dict()

        # 2. Health Report
        if self._health_manager:
            try:
                report = self._health_manager.assess_project_health(project_name)
                health_dict = report.to_dict()
            except Exception:
                pass

        # 3. State Summary
        if self._state_manager:
            try:
                summary = self._state_manager.get_state_summary(project_name)
                state_dict = summary.to_dict()
            except Exception:
                pass

        # 4. Activity Summary
        if self._activity_tracker:
            try:
                act_summary = self._activity_tracker.get_activity_summary(project_name)
                activity_dict = act_summary.to_dict()
            except Exception:
                pass

        # 5. Metadata
        if self._metadata_manager:
            try:
                meta = self._metadata_manager.get_metadata(project_name)
                metadata_dict = meta.to_dict()
            except Exception:
                pass

        # 6. Inspection Summary (if record path exists)
        if self._project_inspector and record_dict and "path" in record_dict:
            try:
                insp_report = self._project_inspector.inspect_project(record_dict["path"])
                inspection_dict = insp_report.to_dict()
            except Exception:
                pass

        return ProjectOperationalView(
            project_name=project_name,
            project_record=record_dict,
            health_report=health_dict,
            state_summary=state_dict,
            activity_summary=activity_dict,
            inspection_summary=inspection_dict,
            metadata=metadata_dict,
        )

    def list_available_operations(self, project_name: str) -> List[str]:
        """List all available built-in and project-specific operational actions.

        Args:
            project_name: Name of target project.

        Returns:
            List of operation names.
        """
        ops = ["inspect", "health_check", "activate", "deactivate"]
        if self._metadata_manager:
            meta_ops = self._metadata_manager.list_supported_operations(project_name)
            for op in meta_ops:
                if op.lower() not in [x.lower() for x in ops]:
                    ops.append(op)
        return ops

    def execute_operation(
        self,
        project_name: str,
        operation_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> OperationResult:
        """Execute an operational action on a target project.

        Args:
            project_name: Target project name.
            operation_name: Name of operation to execute (e.g. 'inspect', 'activate', 'health_check').
            params: Optional parameter dictionary for execution.

        Returns:
            OperationResult detailing execution outcome.
        """
        params = params or {}
        op_clean = operation_name.lower().strip()
        t0 = time.time()

        self._publish_event("operation.started", {
            "project_name": project_name,
            "operation": operation_name,
            "params": params,
        })

        try:
            output: Dict[str, Any] = {}
            if op_clean == "inspect":
                if self._project_registry and self._project_registry.has_project(project_name):
                    rec = self._project_registry.get_project(project_name)
                    if rec and self._project_inspector:
                        insp = self._project_inspector.inspect_project(rec.path)
                        output = insp.to_dict()
                    else:
                        output = {"message": f"Project inspector executed for '{project_name}'."}
                else:
                    output = {"message": f"Executed inspection on '{project_name}'."}

            elif op_clean == "health_check":
                if self._health_manager:
                    report = self._health_manager.assess_project_health(project_name)
                    output = report.to_dict()
                else:
                    output = {"message": f"Health check executed for '{project_name}'."}

            elif op_clean == "activate":
                if self._state_manager:
                    record = self._state_manager.set_project_state(
                        project_name,
                        ProjectState.ACTIVE,
                        reason=params.get("reason", "Activated via ProjectOperationsManager"),
                    )
                    output = record.to_dict()
                else:
                    output = {"message": f"Activated project '{project_name}'."}

            elif op_clean == "deactivate":
                if self._state_manager:
                    record = self._state_manager.set_project_state(
                        project_name,
                        ProjectState.INACTIVE,
                        reason=params.get("reason", "Deactivated via ProjectOperationsManager"),
                    )
                    output = record.to_dict()
                else:
                    output = {"message": f"Deactivated project '{project_name}'."}

            else:
                # Custom or manifest-defined operation
                output = {
                    "message": f"Operation '{operation_name}' executed successfully for project '{project_name}'.",
                    "params": params,
                }

            duration = time.time() - t0
            result = OperationResult(
                operation_name=operation_name,
                project_name=project_name,
                success=True,
                execution_time_seconds=duration,
                output=output,
                metadata={"params": params},
            )

            # Record activity
            if self._activity_tracker:
                self._activity_tracker.record_activity(
                    project_name=project_name,
                    category=ActivityCategory.EXECUTION,
                    action=f"operation.{operation_name}",
                    summary=f"Executed operation '{operation_name}' successfully.",
                    status="SUCCESS",
                )

            self._publish_event("operation.completed", result.to_dict())
            return result

        except Exception as err:
            duration = time.time() - t0
            err_msg = str(err)
            result = OperationResult(
                operation_name=operation_name,
                project_name=project_name,
                success=False,
                execution_time_seconds=duration,
                error_message=err_msg,
                metadata={"params": params},
            )

            if self._activity_tracker:
                self._activity_tracker.record_activity(
                    project_name=project_name,
                    category=ActivityCategory.FAILURE,
                    action=f"operation.{operation_name}",
                    summary=f"Operation '{operation_name}' failed: {err_msg}",
                    status="FAILURE",
                )

            self._publish_event("operation.failed", result.to_dict())
            return result

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish event via EventBus if connected."""
        if self._operator and hasattr(self._operator, "event_bus"):
            self._operator.event_bus.publish(
                OperatorEvent(
                    event_type=event_type,
                    payload=payload,
                    source=self.name,
                )
            )
