"""Unit tests for Project Operations component in Genova Operator."""

from pathlib import Path
import pytest

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.health.manager import ProjectHealthManager
from genova_operator.inspector.manager import ProjectInspector
from genova_operator.metadata.manager import ProjectMetadataManager
from genova_operator.metadata.models import ProjectMetadata
from genova_operator.operations.manager import ProjectOperationsManager
from genova_operator.operations.models import OperationResult, ProjectOperationalView
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import ProjectState


class TestOperationsModels:
    """Test suite for operations models."""

    def test_operational_view_dict_roundtrip(self) -> None:
        view = ProjectOperationalView(
            project_name="GeneFusionAI",
            project_record={"name": "GeneFusionAI", "path": "/path/to/gfai"},
            health_report={"overall_status": "HEALTHY"},
            state_summary={"current_state": "ACTIVE"},
            activity_summary={"total_activities_count": 5},
            inspection_summary={"file_count": 12},
            metadata={"purpose": "Genomics pipeline"},
        )
        data = view.to_dict()
        assert data["project_name"] == "GeneFusionAI"
        assert data["health_report"]["overall_status"] == "HEALTHY"

        deserialized = ProjectOperationalView.from_dict(data)
        assert deserialized.project_name == "GeneFusionAI"
        assert deserialized.state_summary["current_state"] == "ACTIVE"

    def test_operation_result_dict_roundtrip(self) -> None:
        res = OperationResult(
            operation_name="inspect",
            project_name="Clarify",
            success=True,
            execution_time_seconds=0.12,
            output={"status": "complete"},
        )
        data = res.to_dict()
        assert data["operation_name"] == "inspect"
        assert data["success"] is True

        deserialized = OperationResult.from_dict(data)
        assert deserialized.operation_name == "inspect"
        assert deserialized.execution_time_seconds == 0.12


class TestProjectOperationsManager:
    """Test suite for ProjectOperationsManager."""

    def test_lifecycle(self) -> None:
        manager = ProjectOperationsManager()
        assert manager.get_status() == OperatorStatus.UNINITIALIZED
        manager.initialize()
        assert manager.get_status() == OperatorStatus.READY
        manager.shutdown()
        assert manager.get_status() == OperatorStatus.SHUTDOWN

    def test_list_available_operations(self) -> None:
        metadata_mgr = ProjectMetadataManager()
        metadata_mgr.initialize()
        metadata_mgr.set_metadata(
            "GeneFusionAI",
            ProjectMetadata(supported_operations=["train", "evaluate"]),
        )

        ops_mgr = ProjectOperationsManager(metadata_manager=metadata_mgr)
        ops_mgr.initialize()

        ops = ops_mgr.list_available_operations("GeneFusionAI")
        assert "inspect" in ops
        assert "health_check" in ops
        assert "activate" in ops
        assert "deactivate" in ops
        assert "train" in ops
        assert "evaluate" in ops

    def test_get_operational_view_aggregation(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "GeneFusionAI"
        proj_dir.mkdir()
        (proj_dir / "main.py").write_text("# main\n", encoding="utf-8")

        registry = ProjectRegistry(registry_file=tmp_path / "registry.json")
        registry.initialize()
        registry.register_project("GeneFusionAI", proj_dir)

        inspector = ProjectInspector()
        inspector.initialize()

        health_mgr = ProjectHealthManager(project_registry=registry)
        health_mgr.initialize()

        state_mgr = ProjectStateManager(project_registry=registry)
        state_mgr.initialize()

        act_tracker = ProjectActivityTracker()
        act_tracker.initialize()

        meta_mgr = ProjectMetadataManager(project_registry=registry)
        meta_mgr.initialize()

        ops_mgr = ProjectOperationsManager(
            project_registry=registry,
            project_inspector=inspector,
            health_manager=health_mgr,
            state_manager=state_mgr,
            activity_tracker=act_tracker,
            metadata_manager=meta_mgr,
        )
        ops_mgr.initialize()

        view = ops_mgr.get_operational_view("GeneFusionAI")
        assert view.project_name == "GeneFusionAI"
        assert view.project_record is not None
        assert view.health_report is not None
        assert view.health_report["status"] == "HEALTHY"
        assert view.state_summary is not None
        assert view.activity_summary is not None
        assert view.metadata is not None
        assert view.inspection_summary is not None

    def test_execute_built_in_operations(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "Clarify"
        proj_dir.mkdir()
        (proj_dir / "app.py").write_text("# app\n", encoding="utf-8")

        registry = ProjectRegistry(registry_file=tmp_path / "registry.json")
        registry.initialize()
        registry.register_project("Clarify", proj_dir)

        state_mgr = ProjectStateManager(project_registry=registry)
        state_mgr.initialize()

        act_tracker = ProjectActivityTracker()
        act_tracker.initialize()

        ops_mgr = ProjectOperationsManager(
            project_registry=registry,
            state_manager=state_mgr,
            activity_tracker=act_tracker,
        )
        ops_mgr.initialize()

        # Execute activate operation
        res_activate = ops_mgr.execute_operation("Clarify", "activate")
        assert res_activate.success is True
        assert state_mgr.get_project_state("Clarify") == ProjectState.ACTIVE

        # Execute deactivate operation
        res_deactivate = ops_mgr.execute_operation("Clarify", "deactivate")
        assert res_deactivate.success is True
        assert state_mgr.get_project_state("Clarify") == ProjectState.INACTIVE

        # Verify activity was logged
        summary = act_tracker.get_activity_summary("Clarify")
        assert summary.total_activities_count >= 2

    def test_execute_custom_operation_publishes_event(self) -> None:
        op = GenovaOperator()
        op.initialize()

        ops_mgr = ProjectOperationsManager(operator=op)
        ops_mgr.initialize()

        events = []
        op.event_bus.subscribe("operation.started", lambda e: events.append(e))
        op.event_bus.subscribe("operation.completed", lambda e: events.append(e))

        res = ops_mgr.execute_operation("GeneFusionAI", "train", params={"epochs": 5})
        assert res.success is True
        assert len(events) == 2
        assert events[0].event_type == "operation.started"
        assert events[1].event_type == "operation.completed"

        op.shutdown()
