"""ProjectActivityTracker component for Genova Operator.

Tracks recent executions, failures, file changes, running processes, and completed tasks.
Subscribes to EventBus to automatically log events and build project-level activity feeds.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from genova_operator.activity.models import (
    ActivityCategory,
    ActivityEntry,
    ProjectActivitySummary,
)
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus

logger = logging.getLogger(__name__)


class ProjectActivityTracker(BaseComponent):
    """Project Activity Tracker component for Genova Operator.

    Records project activities and feeds activity history to Genova Nexus.
    """

    def __init__(
        self,
        name: str = "project-activity",
        max_entries_per_project: int = 500,
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._max_entries = max_entries_per_project
        self._operator = operator
        self._lock = threading.RLock()
        self._status = OperatorStatus.UNINITIALIZED
        self._activities: Dict[str, List[ActivityEntry]] = defaultdict(list)

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize ProjectActivityTracker and subscribe to EventBus."""
        logger.info("Initializing ProjectActivityTracker (%s)...", self._name)
        with self._lock:
            if self._operator and hasattr(self._operator, "event_bus"):
                self._operator.event_bus.subscribe("*", self._handle_event)
                logger.info("ProjectActivityTracker subscribed to EventBus wildcard.")

            self._status = OperatorStatus.READY
            logger.info("ProjectActivityTracker initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectActivityTracker."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def record_activity(
        self,
        project_name: str,
        category: ActivityCategory,
        action: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ActivityEntry:
        """Record an activity entry for a project.

        Args:
            project_name: Name of target project (e.g. 'GeneFusionAI', 'Clarify').
            category: ActivityCategory enum value.
            action: Specific action performed or event trigger.
            summary: Brief description of activity.
            details: Detail dictionary.
            task_id: Optional associated task ID.
            status: Optional execution status string.

        Returns:
            ActivityEntry instance.
        """
        entry = ActivityEntry(
            project_name=project_name,
            category=category,
            action=action,
            summary=summary,
            details=details or {},
            task_id=task_id,
            status=status,
            timestamp=time.time(),
        )

        with self._lock:
            p_list = self._activities[project_name]
            p_list.append(entry)
            if len(p_list) > self._max_entries:
                self._activities[project_name] = p_list[-self._max_entries:]

        logger.info("Recorded activity for '%s' [%s]: %s", project_name, category.value, summary)
        self._publish_event("activity.recorded", entry.to_dict())
        return entry

    def get_project_activity(
        self,
        project_name: str,
        limit: int = 50,
        category: Optional[ActivityCategory] = None,
    ) -> List[ActivityEntry]:
        """Retrieve recent activity entries for a specific project.

        Args:
            project_name: Name of the project.
            limit: Maximum entries to return.
            category: Optional filter by ActivityCategory.

        Returns:
            List of ActivityEntry instances sorted newest first.
        """
        with self._lock:
            entries = self._activities.get(project_name, [])
            if category:
                entries = [e for e in entries if e.category == category]
            sorted_entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)
            return sorted_entries[:limit]

    def get_activity_summary(self, project_name: str, recent_limit: int = 20) -> ProjectActivitySummary:
        """Generate structured ProjectActivitySummary for Genova Nexus.

        Args:
            project_name: Name of the project.
            recent_limit: Limit of recent entries to include in summary.

        Returns:
            ProjectActivitySummary instance.
        """
        with self._lock:
            entries = self._activities.get(project_name, [])
            failures = sum(1 for e in entries if e.category == ActivityCategory.FAILURE or e.status == "failure")
            last_ts = entries[-1].timestamp if entries else None
            recent = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:recent_limit]

            return ProjectActivitySummary(
                project_name=project_name,
                total_activities_count=len(entries),
                failures_count=failures,
                last_activity_timestamp=last_ts,
                recent_entries=recent,
            )

    def list_all_activity(
        self,
        limit: int = 100,
        category: Optional[ActivityCategory] = None,
    ) -> List[ActivityEntry]:
        """Retrieve workspace-wide activity feed across all projects."""
        with self._lock:
            all_entries: List[ActivityEntry] = []
            for p_list in self._activities.values():
                all_entries.extend(p_list)

            if category:
                all_entries = [e for e in all_entries if e.category == category]

            sorted_entries = sorted(all_entries, key=lambda e: e.timestamp, reverse=True)
            return sorted_entries[:limit]

    def clear_activity(self, project_name: Optional[str] = None) -> None:
        """Clear activity log entries for a project or all projects."""
        with self._lock:
            if project_name:
                self._activities.pop(project_name, None)
            else:
                self._activities.clear()

    def _handle_event(self, event: OperatorEvent) -> None:
        """EventBus handler callback to automatically log system events."""
        if event.source == self.name or event.event_type.startswith("activity."):
            return

        proj_name = event.payload.get("project_name") or event.payload.get("target_project")
        if not proj_name:
            return

        cat = ActivityCategory.EXECUTION
        if "failed" in event.event_type:
            cat = ActivityCategory.FAILURE
        elif "completed" in event.event_type:
            cat = ActivityCategory.TASK_COMPLETED
        elif "submitted" in event.event_type or "started" in event.event_type:
            cat = ActivityCategory.PROCESS_STARTED
        elif "state" in event.event_type:
            cat = ActivityCategory.STATE_CHANGE
        elif "health" in event.event_type:
            cat = ActivityCategory.HEALTH_CHANGE

        self.record_activity(
            project_name=proj_name,
            category=cat,
            action=event.event_type,
            summary=f"Event '{event.event_type}' received from {event.source}",
            details=event.payload,
            task_id=event.payload.get("task_id"),
        )

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish activity events over EventBus if connected."""
        if self._operator and hasattr(self._operator, "event_bus"):
            self._operator.event_bus.publish(
                OperatorEvent(
                    event_type=event_type,
                    payload=payload,
                    source=self.name,
                )
            )
