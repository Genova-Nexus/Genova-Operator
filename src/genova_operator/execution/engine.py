"""CommandExecutionEngine component for Genova Operator.

Provides safe, boundary-enforced process and subprocess command execution with timeout controls,
stdout/stderr streaming, environment isolation, and activity/event tracking.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.activity.models import ActivityCategory
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.execution.models import (
    CommandRequest,
    CommandResult,
    ExecutionStatus,
)
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class CommandExecutionEngine(BaseComponent):
    """Subprocess command execution engine component for Genova Operator.

    Executes CLI commands and scripts safely within workspace boundaries.
    """

    def __init__(
        self,
        name: str = "command-execution",
        workspace_manager: Optional[WorkspaceManager] = None,
        activity_tracker: Optional[ProjectActivityTracker] = None,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._workspace_manager = workspace_manager
        self._activity_tracker = activity_tracker
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize CommandExecutionEngine."""
        logger.info("Initializing CommandExecutionEngine (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("CommandExecutionEngine initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown CommandExecutionEngine."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def run_command(self, request: CommandRequest) -> CommandResult:
        """Execute a command request synchronously with boundary enforcement and timeouts.

        Args:
            request: CommandRequest object.

        Returns:
            CommandResult object detailing execution outcome.
        """
        target_cwd = Path(request.cwd).resolve()

        # Enforce workspace boundary if workspace_manager is available
        if self._workspace_manager:
            try:
                target_cwd = self._workspace_manager.resolve_path(request.cwd)
            except Exception as err:
                err_msg = f"Boundary enforcement error: {err}"
                logger.error(err_msg)
                return CommandResult(
                    command=request.command,
                    exit_code=-1,
                    status=ExecutionStatus.FAILED,
                    error_message=err_msg,
                    metadata=request.metadata,
                )

        if not target_cwd.exists() or not target_cwd.is_dir():
            err_msg = f"Working directory does not exist or is not a directory: {target_cwd}"
            logger.error(err_msg)
            return CommandResult(
                command=request.command,
                exit_code=-1,
                status=ExecutionStatus.FAILED,
                error_message=err_msg,
                metadata=request.metadata,
            )

        # Merge environment variables
        exec_env = os.environ.copy()
        if request.env:
            exec_env.update(request.env)

        # Handle shell vs args list
        use_shell = False
        if isinstance(request.command, str):
            cmd_args: Union[str, List[str]] = request.command
            use_shell = True
        else:
            cmd_args = request.command

        cmd_repr = request.command if isinstance(request.command, str) else " ".join(request.command)
        project_name = request.project_name or target_cwd.name

        logger.info("Executing command '%s' in '%s' (Timeout: %.1fs)...", cmd_repr, target_cwd, request.timeout_seconds)
        self._publish_event("execution.started", {
            "command": cmd_repr,
            "cwd": str(target_cwd),
            "project_name": project_name,
        })

        t0 = time.time()
        try:
            completed = subprocess.run(
                cmd_args,
                cwd=target_cwd,
                env=exec_env,
                timeout=request.timeout_seconds,
                capture_output=True,
                text=True,
                shell=use_shell,
            )
            duration = time.time() - t0
            success = completed.returncode == 0
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            cmd_err_msg: Optional[str] = None if success else f"Command failed with exit code {completed.returncode}."

            result = CommandResult(
                command=request.command,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                duration_seconds=duration,
                status=status,
                error_message=cmd_err_msg,
                metadata=request.metadata,
            )

            # Record activity
            if self._activity_tracker:
                cat = ActivityCategory.EXECUTION if success else ActivityCategory.FAILURE
                self._activity_tracker.record_activity(
                    project_name=project_name,
                    category=cat,
                    action="command_execution",
                    summary=f"Executed '{cmd_repr}' (exit code {completed.returncode})",
                    status="SUCCESS" if success else "FAILURE",
                )

            event_type = "execution.completed" if success else "execution.failed"
            self._publish_event(event_type, result.to_dict())
            return result

        except subprocess.TimeoutExpired as err:
            duration = time.time() - t0
            err_msg = f"Command execution timed out after {request.timeout_seconds} seconds."
            logger.warning("Command '%s' timed out in %s.", cmd_repr, target_cwd)

            stdout = err.stdout.decode("utf-8", errors="replace") if isinstance(err.stdout, bytes) else (err.stdout or "")
            stderr = err.stderr.decode("utf-8", errors="replace") if isinstance(err.stderr, bytes) else (err.stderr or "")

            result = CommandResult(
                command=request.command,
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                status=ExecutionStatus.TIMED_OUT,
                error_message=err_msg,
                metadata=request.metadata,
            )

            if self._activity_tracker:
                self._activity_tracker.record_activity(
                    project_name=project_name,
                    category=ActivityCategory.FAILURE,
                    action="command_execution",
                    summary=f"Command '{cmd_repr}' timed out after {request.timeout_seconds}s",
                    status="TIMED_OUT",
                )

            self._publish_event("execution.timed_out", result.to_dict())
            return result

        except Exception as err:
            duration = time.time() - t0
            err_msg = str(err)
            logger.error("Failed to execute command '%s': %s", cmd_repr, err_msg)

            result = CommandResult(
                command=request.command,
                exit_code=-1,
                duration_seconds=duration,
                status=ExecutionStatus.FAILED,
                error_message=err_msg,
                metadata=request.metadata,
            )

            if self._activity_tracker:
                self._activity_tracker.record_activity(
                    project_name=project_name,
                    category=ActivityCategory.FAILURE,
                    action="command_execution",
                    summary=f"Command execution error: {err_msg}",
                    status="FAILURE",
                )

            self._publish_event("execution.failed", result.to_dict())
            return result

    def run_simple_command(
        self,
        command: Union[str, List[str]],
        cwd: Union[str, Path] = ".",
        timeout_seconds: float = 60.0,
        project_name: Optional[str] = None,
    ) -> CommandResult:
        """Helper to run a simple command without constructing CommandRequest explicitly."""
        req = CommandRequest(
            command=command,
            cwd=str(cwd),
            timeout_seconds=timeout_seconds,
            project_name=project_name,
        )
        return self.run_command(req)

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
