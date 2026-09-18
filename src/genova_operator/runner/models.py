"""Subprocess Runner data models for Genova Operator.

Defines standardized schemas for background process handles, status enums, and log tracking.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ProcessStatus(Enum):
    """Status enum for managed background subprocesses."""
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    KILLED = "KILLED"


@dataclass
class SubprocessHandle:
    """Handle model representing a managed background subprocess.

    Attributes:
        process_id: Unique process identifier string.
        pid: OS Process ID (PID) if running.
        command: Executed command string or list.
        cwd: Working directory path.
        start_time: Start timestamp in seconds.
        end_time: Optional completion timestamp in seconds.
        status: ProcessStatus enum value.
        log_file: Optional path to stdout/stderr output log file.
        project_name: Target project name.
        exit_code: Process exit code if completed.
        metadata: Arbitrary metadata dictionary.
    """
    process_id: str
    command: Union[str, List[str]]
    cwd: str
    pid: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: ProcessStatus = ProcessStatus.STARTING
    log_file: Optional[str] = None
    project_name: Optional[str] = None
    exit_code: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_alive(self) -> bool:
        """Return True if process status is STARTING or RUNNING."""
        return self.status in (ProcessStatus.STARTING, ProcessStatus.RUNNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "pid": self.pid,
            "command": self.command,
            "cwd": self.cwd,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "is_alive": self.is_alive,
            "log_file": self.log_file,
            "project_name": self.project_name,
            "exit_code": self.exit_code,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubprocessHandle:
        status_val = data.get("status", ProcessStatus.STARTING.value)
        try:
            status_enum = ProcessStatus(status_val)
        except ValueError:
            status_enum = ProcessStatus.FAILED

        return cls(
            process_id=str(data.get("process_id", "")),
            pid=data.get("pid"),
            command=data.get("command", ""),
            cwd=str(data.get("cwd", ".")),
            start_time=float(data.get("start_time", time.time())),
            end_time=data.get("end_time"),
            status=status_enum,
            log_file=data.get("log_file"),
            project_name=data.get("project_name"),
            exit_code=data.get("exit_code"),
            metadata=dict(data.get("metadata", {})),
        )
