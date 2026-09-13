"""Unit tests for Genova Operator Project Activity."""

import pytest
from pathlib import Path

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.activity.models import ActivityCategory, ActivityEntry, ProjectActivitySummary
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus


def test_activity_models_and_serialization() -> None:
    """Test ActivityEntry and ProjectActivitySummary serialization."""
    entry = ActivityEntry(
        project_name="GeneFusionAI",
        category=ActivityCategory.EXECUTION,
        action="train_model",
        summary="Model training started",
        details={"epoch": 1},
        task_id="task-99",
        status="running",
    )
    assert entry.project_name == "GeneFusionAI"
    data = entry.to_dict()
    assert data["category"] == "EXECUTION"
    assert data["task_id"] == "task-99"

    restored = ActivityEntry.from_dict(data)
    assert restored.action == "train_model"
    assert restored.category == ActivityCategory.EXECUTION

    summary = ProjectActivitySummary(
        project_name="GeneFusionAI",
        total_activities_count=5,
        failures_count=1,
        recent_entries=[entry],
    )
    s_data = summary.to_dict()
    assert s_data["total_activities_count"] == 5
    assert s_data["failures_count"] == 1


def test_manual_activity_recording_and_querying() -> None:
    """Test recording and querying activities for GeneFusionAI and Clarify."""
    tracker = ProjectActivityTracker()
    tracker.initialize()

    tracker.record_activity(
        project_name="GeneFusionAI",
        category=ActivityCategory.EXECUTION,
        action="train",
        summary="Model training",
    )
    tracker.record_activity(
        project_name="GeneFusionAI",
        category=ActivityCategory.FAILURE,
        action="train",
        summary="Out of memory",
        status="failure",
    )
    tracker.record_activity(
        project_name="Clarify",
        category=ActivityCategory.CHANGE,
        action="update_config",
        summary="Updated config",
    )

    gf_entries = tracker.get_project_activity("GeneFusionAI")
    assert len(gf_entries) == 2

    gf_failures = tracker.get_project_activity("GeneFusionAI", category=ActivityCategory.FAILURE)
    assert len(gf_failures) == 1
    assert gf_failures[0].summary == "Out of memory"

    summary = tracker.get_activity_summary("GeneFusionAI")
    assert summary.total_activities_count == 2
    assert summary.failures_count == 1

    all_entries = tracker.list_all_activity()
    assert len(all_entries) == 3


def test_event_bus_autotracking() -> None:
    """Test automatic event logging over EventBus."""
    operator = GenovaOperator()
    tracker = ProjectActivityTracker(operator=operator)

    operator.register_component(tracker)
    operator.initialize()

    # Emit event over EventBus
    operator.event_bus.publish(
        OperatorEvent(
            event_type="task.completed",
            payload={"project_name": "Clarify", "task_id": "task-200"},
            source="runner",
        )
    )

    entries = tracker.get_project_activity("Clarify")
    assert len(entries) == 1
    assert entries[0].category == ActivityCategory.TASK_COMPLETED
    assert entries[0].task_id == "task-200"


def test_activity_tracker_component_integration() -> None:
    """Test registering ProjectActivityTracker with GenovaOperator core."""
    operator = GenovaOperator()
    tracker = ProjectActivityTracker()

    operator.register_component(tracker)
    operator.initialize()

    assert operator.has_component("project-activity")
    retrieved = operator.get_component("project-activity")
    assert isinstance(retrieved, ProjectActivityTracker)
    assert retrieved.get_status() == OperatorStatus.READY
