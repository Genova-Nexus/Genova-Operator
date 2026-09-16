"""End-to-End Phase 2 Integration Test Suite for Genova Operator.

Validates complete integration of Phase 2 Project Operations components:
- ProjectInspector (Day 8)
- ProjectHealthManager (Day 9)
- ProjectStateManager (Day 10)
- ProjectActivityTracker (Day 11)
- ProjectMetadataManager (Day 12)
- ProjectOperationsManager (Day 13)
- ProjectAdapters (Day 14)
against GeneFusionAI and Clarify sample projects.
"""

import json
from pathlib import Path
import pytest

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.adapters.manager import ProjectAdapterRegistry
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.health.manager import ProjectHealthManager
from genova_operator.inspector.manager import ProjectInspector
from genova_operator.metadata.manager import ProjectMetadataManager
from genova_operator.operations.manager import ProjectOperationsManager
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import ProjectState
from genova_operator.workspace.manager import WorkspaceManager


def test_phase2_project_operations_e2e(tmp_path: Path) -> None:
    """Complete Phase 2 E2E integration validation test."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    # 1. Setup sample projects: GeneFusionAI & Clarify
    gf_dir = workspace_dir / "GeneFusionAI"
    gf_dir.mkdir()
    (gf_dir / "main.py").write_text("# GeneFusionAI main entry point\n", encoding="utf-8")
    (gf_dir / "requirements.txt").write_text("torch>=2.0.0\npandas\n", encoding="utf-8")
    (gf_dir / "genova_project.json").write_text(
        json.dumps({
            "purpose": "Gene Fusion AI genomics pipeline",
            "technologies": ["Python", "PyTorch"],
            "operations": ["detect_fusions", "train_model"],
            "adapter": "GeneFusionAI",
        }),
        encoding="utf-8",
    )

    clarify_dir = workspace_dir / "Clarify"
    clarify_dir.mkdir()
    (clarify_dir / "app.py").write_text("# Clarify app entry point\n", encoding="utf-8")
    (clarify_dir / "requirements.txt").write_text("fastapi\nopencv-python\n", encoding="utf-8")
    (clarify_dir / "genova_project.json").write_text(
        json.dumps({
            "purpose": "Medical imaging report clarification",
            "technologies": ["Python", "FastAPI"],
            "operations": ["analyze_image", "generate_report"],
            "adapter": "Clarify",
        }),
        encoding="utf-8",
    )

    # 2. Instantiate GenovaOperator & Phase 2 Sub-components
    operator = GenovaOperator()
    operator.initialize()

    ws_mgr = WorkspaceManager(root_path=workspace_dir)
    ws_mgr.initialize()

    registry_file = tmp_path / "registry.json"
    registry = ProjectRegistry(registry_file=registry_file)
    registry.initialize()
    registry.register_project("GeneFusionAI", gf_dir)
    registry.register_project("Clarify", clarify_dir)

    inspector = ProjectInspector()
    inspector.initialize()

    health_mgr = ProjectHealthManager(
        project_registry=registry,
        project_inspector=inspector,
        workspace_manager=ws_mgr,
    )
    health_mgr.initialize()

    state_mgr = ProjectStateManager(
        project_registry=registry,
        project_health_manager=health_mgr,
        operator=operator,
    )
    state_mgr.initialize()

    act_tracker = ProjectActivityTracker(operator=operator)
    act_tracker.initialize()

    meta_mgr = ProjectMetadataManager(
        project_registry=registry,
        workspace_manager=ws_mgr,
        operator=operator,
    )
    meta_mgr.initialize()

    adapter_reg = ProjectAdapterRegistry(operator=operator)
    adapter_reg.initialize()

    ops_mgr = ProjectOperationsManager(
        project_registry=registry,
        project_inspector=inspector,
        health_manager=health_mgr,
        state_manager=state_mgr,
        activity_tracker=act_tracker,
        metadata_manager=meta_mgr,
        operator=operator,
    )
    ops_mgr.initialize()

    # 3. Perform Project Inspection
    gf_insp = inspector.inspect_project(gf_dir)
    assert gf_insp.project_name == "GeneFusionAI"
    assert "torch" in gf_insp.dependencies.frameworks

    clarify_insp = inspector.inspect_project(clarify_dir)
    assert clarify_insp.project_name == "Clarify"

    # 4. 5-Pillar Health Assessments
    gf_health = health_mgr.assess_project_health("GeneFusionAI")
    assert gf_health.is_healthy is True
    assert gf_health.health_score >= 80.0

    clarify_health = health_mgr.assess_project_health("Clarify")
    assert clarify_health.is_healthy is True

    # 5. State Management & Transitions
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.AVAILABLE
    state_mgr.set_project_state("GeneFusionAI", ProjectState.ACTIVE, reason="Phase 2 E2E Test")
    assert state_mgr.get_project_state("GeneFusionAI") == ProjectState.ACTIVE

    # 6. Consolidated Operational Views
    gf_view = ops_mgr.get_operational_view("GeneFusionAI")
    assert gf_view.project_name == "GeneFusionAI"
    assert gf_view.health_report["status"] == "HEALTHY"
    assert gf_view.metadata["purpose"] == "Gene Fusion AI genomics pipeline"

    clarify_view = ops_mgr.get_operational_view("Clarify")
    assert clarify_view.project_name == "Clarify"
    assert clarify_view.metadata["purpose"] == "Medical imaging report clarification"

    # 7. Operational Execution
    res_activate = ops_mgr.execute_operation("GeneFusionAI", "activate")
    assert res_activate.success is True

    res_detect = adapter_reg.execute_action(gf_dir, "detect_fusions", {"sample_id": "HG002_E2E"})
    assert res_detect["status"] == "COMPLETED"

    res_report = adapter_reg.execute_action(clarify_dir, "generate_report", {"patient_id": "P99"})
    assert res_report["status"] == "COMPLETED"

    # 8. Activity Log Verification
    gf_act_summary = act_tracker.get_activity_summary("GeneFusionAI")
    assert gf_act_summary.total_activities_count >= 1

    # 9. Clean Shutdown
    ops_mgr.shutdown()
    adapter_reg.shutdown()
    meta_mgr.shutdown()
    act_tracker.shutdown()
    state_mgr.shutdown()
    health_mgr.shutdown()
    inspector.shutdown()
    registry.shutdown()
    ws_mgr.shutdown()
    operator.shutdown()
