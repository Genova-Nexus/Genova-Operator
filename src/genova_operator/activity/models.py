"""Project Activity models for Genova Operator.

Defines activity categories, individual activity log entries, and project-level activity summaries
consumed by Genova Nexus.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActivityCategory(Enum):
    """Category classification of project activities."""
    EXECUTION = "EXECUTION"
    FAILURE = "FAILURE"
    CHANGE = "CHANGE"
    PROCESS_STARTED = "PROCESS_STARTED"
    PROCESS_STOPPED = "PROCESS_STOPPED"
    TASK_COMPLETED = "TASK_COMPLETED"
    HEALTH_CHANGE = "HEALTH_CHANGE"
    STATE_CHANGE = "STATE_CHANGE"


@dataclass
class ActivityEntry:
    """Individual activity log entry.

    Attributes:
        project_name: Target project name.
        category: ActivityCategory enum value.
        action: Specific action performed or event trigger.
        summary: Brief human-readable description.
        details: Arbitrary detail dictionary.
        task_id: Optional associated task ID.
        status: Optional status string ('success', 'failure', 'pending').
        entry_id: Unique entry UUID string.
        timestamp: Epoch timestamp when activity occurred.
    """
    project_name: str
    category: ActivityCategory
    action: str
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    status: Optional[str] = None
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "project_name": self.project_name,
            "category": self.category.value,
            "action": self.action,
            "summary": self.summary,
            "details": self.details,
            "task_id": self.task_id,
            "status": self.status,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActivityEntry:
        return cls(
            entry_id=data.get("entry_id", str(uuid.uuid4())),
            project_name=data["project_name"],
            category=ActivityCategory(data["category"]),
            action=data["action"],
            summary=data["summary"],
            details=dict(data.get("details", {})),
            task_id=data.get("task_id"),
            status=data.get("status"),
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class ProjectActivitySummary:
    """Project-level activity view consumed by Genova Nexus.

    Attributes:
        project_name: Name of the project.
        total_activities_count: Total entries recorded.
        failures_count: Total failure entries recorded.
        last_activity_timestamp: Timestamp of the most recent activity.
        recent_entries: List of recent ActivityEntry objects.
    """
    project_name: str
    total_activities_count: int = 0
    failures_count: int = 0
    last_activity_timestamp: Optional[float] = None
    recent_entries: List[ActivityEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "total_activities_count": self.total_activities_count,
            "failures_count": self.failures_count,
            "last_activity_timestamp": self.last_activity_timestamp,
            "recent_entries_count": len(self.recent_entries),
            "recent_entries": [e.to_dict() for e in self.recent_entries],
        }
