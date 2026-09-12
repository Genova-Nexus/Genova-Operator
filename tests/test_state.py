"""Unit tests for Genova Operator Project State."""

import pytest
from pathlib import Path

from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.health.models import HealthStatus, ProjectHealthReport
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import ProjectState, ProjectStateSummary, StateTransitionRecord


def test_project_state_models_and_summary() -> None:
    """Test StateTransitionRecord and ProjectStateSummary models."""
    record = StateTransitionRecord(
        project_name="GeneFusionAI",
        previous_state=ProjectState.AVAILABLE,
        new_state=ProjectState.RUNNING,
        reason="Task task-101 started",
        task_id="task-101",
    )
    assert record.project_name == "GeneFusionAI"
    assert record.new_state == ProjectState.RUNNING
    data = record.to_dict()
    assert data["previous_state"] == "AVAILABLE"
    assert data["new_state"] == "RUNNING"

    summary = ProjectStateSummary(
        project_name="GeneFusionAI",
        current_state=ProjectState.RUNNING,
        active_tasks=["task-101"],
        history=[record],
    )
    assert summary.is_running is True
    s_data = summary.to_dict()
    assert s_data["is_running"] is True
    assert s_data["history_count"] == 1


def test_state_transitions_and_task_coupling() -> None:
    """Test state transitions and active task association."""
    state_mgr = ProjectStateManager()
    state_mgr.initialize()

    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.AVAILABLE

    # Associate task 1
    t1 = state_mgr.associate_task("GeneFusionAI", "task-1")
    assert t1.new_state == ProjectState.RUNNING
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.RUNNING

    # Associate task 2
    state_mgr.associate_task("GeneFusionAI", "task-2")
    summary = state_mgr.get_state_summary("GeneFusionAI")
    assert len(summary.active_tasks) == 2

    # Disassociate task 1 -> should stay RUNNING because task 2 active
    state_mgr.disassociate_task("GeneFusionAI", "task-1")
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.RUNNING

    # Disassociate task 2 -> should revert to ACTIVE
    t2 = state_mgr.disassociate_task("GeneFusionAI", "task-2", fallback_state=ProjectState.ACTIVE)
    assert t2.new_state == ProjectState.ACTIVE
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.ACTIVE


def test_health_sync() -> None:
    """Test updating project state based on a ProjectHealthReport."""
    state_mgr = ProjectStateManager()
    state_mgr.initialize()

    # Unavailable report
    unavail_report = ProjectHealthReport(
        project_name="GeneFusionAI",
        project_path="/missing/path",
        status=HealthStatus.UNAVAILABLE,
    )
    t = state_mgr.update_from_health("GeneFusionAI", unavail_report)
    assert t.new_state == ProjectState.UNAVAILABLE
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.UNAVAILABLE

    # Healthy report
    healthy_report = ProjectHealthReport(
        project_name="GeneFusionAI",
        project_path="/valid/path",
        status=HealthStatus.HEALTHY,
    )
    t2 = state_mgr.update_from_health("GeneFusionAI", healthy_report)
    assert t2.new_state == ProjectState.AVAILABLE


def test_event_bus_notifications() -> None:
    """Test publishing state.changed events over EventBus."""
    operator = GenovaOperator()
    events_received = []

    def handler(event: OperatorEvent) -> None:
        events_received.append(event)

    operator.event_bus.subscribe("state.changed", handler)

    state_mgr = ProjectStateManager(operator=operator)
    operator.register_component(state_mgr)
    operator.initialize()

    state_mgr.set_project_state("Clarify", ProjectState.ACTIVE, reason="accessed")

    assert len(events_received) == 1
    assert events_received[0].payload["project_name"] == "Clarify"
    assert events_received[0].payload["new_state"] == "ACTIVE"


def test_state_manager_component_integration() -> None:
    """Test registering ProjectStateManager with GenovaOperator core."""
    operator = GenovaOperator()
    registry = ProjectRegistry()
    registry.register_project("Clarify", "projects/Clarify")

    state_mgr = ProjectStateManager(project_registry=registry)
    operator.register_component(registry)
    operator.register_component(state_mgr)
    operator.initialize()

    assert operator.has_component("project-state")
    retrieved = operator.get_component("project-state")
    assert isinstance(retrieved, ProjectStateManager)
    assert retrieved.get_status() == OperatorStatus.READY
    assert retrieved.get_project_state("Clarify") == ProjectState.AVAILABLE
