"""SubprocessRunner component for Genova Operator.

Manages background process spawning, PID tracking, process termination, output log streaming,
and integration with ProjectStateManager and ProjectActivityTracker.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.activity.models import ActivityCategory
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.runner.models import ProcessStatus, SubprocessHandle
from genova_operator.state.manager import ProjectStateManager
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class SubprocessRunner(BaseComponent):
    """Background task runner and subprocess manager component for Genova Operator."""

    def __init__(
        self,
        name: str = "subprocess-runner",
        workspace_manager: Optional[WorkspaceManager] = None,
        state_manager: Optional[ProjectStateManager] = None,
        activity_tracker: Optional[ProjectActivityTracker] = None,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._workspace_manager = workspace_manager
        self._state_manager = state_manager
        self._activity_tracker = activity_tracker
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED
        self._lock = threading.RLock()
        self._processes: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize SubprocessRunner."""
        logger.info("Initializing SubprocessRunner (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("SubprocessRunner initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown SubprocessRunner and stop all managed background processes."""
        logger.info("Shutting down SubprocessRunner (%s)...", self._name)
        with self._lock:
            for proc_id in list(self._processes.keys()):
                try:
                    self.stop_process(proc_id, timeout_seconds=2.0)
                except Exception as err:
                    logger.warning("Error stopping process '%s' during shutdown: %s", proc_id, err)
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def start_process(
        self,
        command: Union[str, List[str]],
        cwd: Union[str, Path] = ".",
        project_name: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> SubprocessHandle:
        """Spawn a background subprocess, redirect logs, and track PID.

        Args:
            command: Command string or list of arguments.
            cwd: Working directory path.
            project_name: Optional target project name.
            env: Optional environment variable overrides.

        Returns:
            SubprocessHandle object.
        """
        target_cwd = Path(cwd).resolve()
        if self._workspace_manager:
            try:
                target_cwd = self._workspace_manager.resolve_path(cwd)
            except Exception as err:
                logger.error("Boundary enforcement error in start_process: %s", err)
                raise

        if not target_cwd.exists() or not target_cwd.is_dir():
            raise ValueError(f"Working directory does not exist: {target_cwd}")

        process_id = uuid.uuid4().hex[:12]
        proj_name = project_name or target_cwd.name

        # Prepare log directory & file
        log_dir = target_cwd / ".genova" / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            log_dir = target_cwd / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / f"{process_id}.log"
        log_file_obj = open(log_path, "a", encoding="utf-8")

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        use_shell = isinstance(command, str)
        cmd_repr = command if isinstance(command, str) else " ".join(command)

        logger.info("Spawning background process '%s' (ID: %s) in '%s'...", cmd_repr, process_id, target_cwd)

        try:
            popen = subprocess.Popen(
                command,
                cwd=target_cwd,
                env=exec_env,
                stdout=log_file_obj,
                stderr=subprocess.STDOUT,
                shell=use_shell,
            )
        except Exception as err:
            log_file_obj.close()
            logger.error("Failed to spawn process '%s': %s", cmd_repr, err)
            raise

        handle = SubprocessHandle(
            process_id=process_id,
            pid=popen.pid,
            command=command,
            cwd=str(target_cwd),
            start_time=time.time(),
            status=ProcessStatus.RUNNING,
            log_file=str(log_path),
            project_name=proj_name,
        )

        with self._lock:
            self._processes[process_id] = {
                "handle": handle,
                "popen": popen,
                "log_file_obj": log_file_obj,
            }

        # Associate task with ProjectStateManager
        if self._state_manager and proj_name:
            try:
                self._state_manager.associate_task(proj_name, process_id)
            except Exception as err:
                logger.warning("Could not associate task '%s' with state manager: %s", process_id, err)

        # Record activity
        if self._activity_tracker and proj_name:
            self._activity_tracker.record_activity(
                project_name=proj_name,
                category=ActivityCategory.PROCESS_STARTED,
                action="subprocess.started",
                summary=f"Started background process '{cmd_repr}' (PID {popen.pid})",
                task_id=process_id,
                status="RUNNING",
            )

        self._publish_event("subprocess.started", handle.to_dict())
        return handle

    def get_process(self, process_id: str) -> Optional[SubprocessHandle]:
        """Fetch SubprocessHandle and update status by polling process."""
        with self._lock:
            if process_id not in self._processes:
                return None
            return self._update_process_status(process_id)

    def list_processes(self, project_name: Optional[str] = None) -> List[SubprocessHandle]:
        """List all managed subprocess handles, optionally filtered by project_name."""
        handles: List[SubprocessHandle] = []
        with self._lock:
            for proc_id in list(self._processes.keys()):
                handle = self._update_process_status(proc_id)
                if handle:
                    if project_name is None or handle.project_name == project_name:
                        handles.append(handle)
        return handles

    def stop_process(self, process_id: str, timeout_seconds: float = 5.0) -> SubprocessHandle:
        """Gracefully terminate a running background subprocess.

        Args:
            process_id: Unique process ID.
            timeout_seconds: Seconds to wait for graceful SIGTERM before SIGKILL.

        Returns:
            Updated SubprocessHandle.
        """
        with self._lock:
            if process_id not in self._processes:
                raise ValueError(f"Process ID '{process_id}' not found.")

            entry = self._processes[process_id]
            handle: SubprocessHandle = entry["handle"]
            popen: subprocess.Popen[Any] = entry["popen"]
            log_file_obj = entry.get("log_file_obj")

            if handle.is_alive and popen.poll() is None:
                logger.info("Stopping background process '%s' (PID %s)...", process_id, popen.pid)
                popen.terminate()
                try:
                    popen.wait(timeout=timeout_seconds)
                    handle.status = ProcessStatus.STOPPED
                except subprocess.TimeoutExpired:
                    logger.warning("Process '%s' did not terminate in %.1fs. Force killing...", process_id, timeout_seconds)
                    popen.kill()
                    popen.wait()
                    handle.status = ProcessStatus.KILLED

                handle.exit_code = popen.returncode
                handle.end_time = time.time()

                if log_file_obj and not log_file_obj.closed:
                    log_file_obj.close()

                if self._state_manager and handle.project_name:
                    try:
                        self._state_manager.disassociate_task(handle.project_name, process_id)
                    except Exception:
                        pass

                if self._activity_tracker and handle.project_name:
                    self._activity_tracker.record_activity(
                        project_name=handle.project_name,
                        category=ActivityCategory.PROCESS_STOPPED,
                        action="subprocess.stopped",
                        summary=f"Stopped process '{process_id}' (PID {handle.pid})",
                        task_id=process_id,
                        status=handle.status.value,
                    )

                self._publish_event("subprocess.stopped", handle.to_dict())

            return handle

    def tail_logs(self, process_id: str, max_lines: int = 100) -> str:
        """Read trailing log output lines for a managed process.

        Args:
            process_id: Process ID.
            max_lines: Maximum trailing lines to read (default 100).

        Returns:
            Log text string.
        """
        handle = self.get_process(process_id)
        if not handle or not handle.log_file:
            return ""

        log_path = Path(handle.log_file)
        if not log_path.is_file():
            return ""

        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-max_lines:])
        except Exception as err:
            logger.error("Error reading log file '%s': %s", log_path, err)
            return ""

    def _update_process_status(self, process_id: str) -> Optional[SubprocessHandle]:
        """Internal poll and update helper."""
        if process_id not in self._processes:
            return None

        entry = self._processes[process_id]
        handle: SubprocessHandle = entry["handle"]
        popen: subprocess.Popen[Any] = entry["popen"]
        log_file_obj = entry.get("log_file_obj")

        if handle.is_alive:
            retcode = popen.poll()
            if retcode is not None:
                handle.exit_code = retcode
                handle.end_time = time.time()
                handle.status = ProcessStatus.COMPLETED if retcode == 0 else ProcessStatus.FAILED

                if log_file_obj and not log_file_obj.closed:
                    log_file_obj.close()

                if self._state_manager and handle.project_name:
                    try:
                        self._state_manager.disassociate_task(handle.project_name, process_id)
                    except Exception:
                        pass

                if self._activity_tracker and handle.project_name:
                    cat = ActivityCategory.EXECUTION if retcode == 0 else ActivityCategory.FAILURE
                    self._activity_tracker.record_activity(
                        project_name=handle.project_name,
                        category=cat,
                        action="subprocess.completed",
                        summary=f"Process '{process_id}' finished with exit code {retcode}",
                        task_id=process_id,
                        status="COMPLETED" if retcode == 0 else "FAILED",
                    )

                event_type = "subprocess.completed" if retcode == 0 else "subprocess.failed"
                self._publish_event(event_type, handle.to_dict())

        return handle

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
