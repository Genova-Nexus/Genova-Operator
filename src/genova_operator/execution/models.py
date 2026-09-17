"""Execution Engine data models for Genova Operator.

Defines standardized schemas for execution requests, execution results, and status enums.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ExecutionStatus(Enum):
    """Status enum for process and task executions."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


@dataclass
class CommandRequest:
    """Command execution request model.

    Attributes:
        command: Command string or list of command arguments.
        cwd: Target working directory.
        env: Optional environment variable overrides.
        timeout_seconds: Maximum execution duration in seconds (default 60.0).
        project_name: Optional target project name.
        metadata: Arbitrary key-value metadata dictionary.
    """
    command: Union[str, List[str]]
    cwd: str
    env: Optional[Dict[str, str]] = None
    timeout_seconds: float = 60.0
    project_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "cwd": self.cwd,
            "env": self.env,
            "timeout_seconds": self.timeout_seconds,
            "project_name": self.project_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CommandRequest:
        return cls(
            command=data.get("command", ""),
            cwd=str(data.get("cwd", ".")),
            env=data.get("env"),
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            project_name=data.get("project_name"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class CommandResult:
    """Command execution result model.

    Attributes:
        command: Command string or list executed.
        exit_code: Process return code (-1 if timed out/failed to launch).
        stdout: Standard output string.
        stderr: Standard error string.
        duration_seconds: Floating point execution time.
        status: ExecutionStatus enum value.
        error_message: Optional error message string.
        metadata: Result metadata dictionary.
        timestamp: ISO timestamp string of completion.
    """
    command: Union[str, List[str]]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": round(self.duration_seconds, 4),
            "status": self.status.value,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CommandResult:
        status_val = data.get("status", ExecutionStatus.SUCCESS.value)
        try:
            status_enum = ExecutionStatus(status_val)
        except ValueError:
            status_enum = ExecutionStatus.FAILED

        return cls(
            command=data.get("command", ""),
            exit_code=int(data.get("exit_code", -1)),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
            status=status_enum,
            error_message=data.get("error_message"),
            metadata=dict(data.get("metadata", {})),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )
