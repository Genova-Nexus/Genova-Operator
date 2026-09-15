"""Project Operations models for Genova Operator.

Defines standardized schemas for consolidated project operational views and operation execution results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectOperationalView:
    """Consolidated operational snapshot model for a project.

    Aggregates project record, health report, state summary, activity summary,
    inspection summary, and metadata into a single unified operational view.
    """
    project_name: str
    project_record: Optional[Dict[str, Any]] = None
    health_report: Optional[Dict[str, Any]] = None
    state_summary: Optional[Dict[str, Any]] = None
    activity_summary: Optional[Dict[str, Any]] = None
    inspection_summary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_record": self.project_record,
            "health_report": self.health_report,
            "state_summary": self.state_summary,
            "activity_summary": self.activity_summary,
            "inspection_summary": self.inspection_summary,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectOperationalView:
        return cls(
            project_name=str(data.get("project_name", "")),
            project_record=data.get("project_record"),
            health_report=data.get("health_report"),
            state_summary=data.get("state_summary"),
            activity_summary=data.get("activity_summary"),
            inspection_summary=data.get("inspection_summary"),
            metadata=data.get("metadata"),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )


@dataclass
class OperationResult:
    """Standardized result model for project-level operation executions."""
    operation_name: str
    project_name: str
    success: bool
    execution_time_seconds: float = 0.0
    output: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_name": self.operation_name,
            "project_name": self.project_name,
            "success": self.success,
            "execution_time_seconds": self.execution_time_seconds,
            "output": self.output,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OperationResult:
        return cls(
            operation_name=str(data.get("operation_name", "")),
            project_name=str(data.get("project_name", "")),
            success=bool(data.get("success", False)),
            execution_time_seconds=float(data.get("execution_time_seconds", 0.0)),
            output=dict(data.get("output", {})),
            error_message=data.get("error_message"),
            metadata=dict(data.get("metadata", {})),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )
