"""End-to-end foundation integration test for Phase 1 (Days 1–7).

Validates that Core, Config, Workspace, Registry, Discovery, and Diagnostics work
seamlessly together against GeneFusionAI and Clarify workloads.
"""

import json
import pytest
from pathlib import Path

from genova_operator import (
    ConfigManager,
    CoreDiagnostics,
    GenovaOperator,
    ProjectConfig,
    ProjectDiscovery,
    ProjectRegistry,
    TaskRequest,
    TaskState,
    WorkspaceManager,
)


def test_phase1_foundation_e2e(tmp_path: Path) -> None:
    """Full End-to-End Phase 1 Foundation test.

    Verifies:
    1. Workspace setup with candidate project folders (GeneFusionAI and Clarify).
    2. Configuration initialization and per-project isolation.
    3. Automatic project discovery & auto-registration into ProjectRegistry.
    4. Task dispatching via GenovaOperator orchestrator.
    5. CoreDiagnostics system health check report.
    """
    # 1. Setup workspace & project folders
    workspace_root = tmp_path / "genova_workspace"
    projects_dir = workspace_root / "projects"
    projects_dir.mkdir(parents=True)

    # Setup GeneFusionAI project
    gf_dir = projects_dir / "GeneFusionAI"
    gf_dir.mkdir()
    with open(gf_dir / "genova_project.json", "w", encoding="utf-8") as f:
        json.dump({"name": "GeneFusionAI", "type": "ml_research"}, f)
    (gf_dir / "pyproject.toml").touch()
    (gf_dir / "requirements.txt").touch()

    # Setup Clarify project
    cl_dir = projects_dir / "Clarify"
    cl_dir.mkdir()
    with open(cl_dir / "genova_project.json", "w", encoding="utf-8") as f:
        json.dump({"name": "Clarify", "type": "research"}, f)
    (cl_dir / "requirements.txt").touch()

    # 2. Instantiate and register components
    operator = GenovaOperator(name="genova-operator-foundation")
    config_mgr = ConfigManager()
    config_mgr.config.workspace.root_path = str(workspace_root)
    ws_mgr = WorkspaceManager(root_path=workspace_root, projects_dir="projects", config_manager=config_mgr)
    registry = ProjectRegistry()
    discovery = ProjectDiscovery(workspace_manager=ws_mgr, project_registry=registry)
    diagnostics = CoreDiagnostics(operator=operator)

    operator.register_component(config_mgr)
    operator.register_component(ws_mgr)
    operator.register_component(registry)
    operator.register_component(discovery)
    operator.register_component(diagnostics)

    operator.initialize()

    # 3. Configure project options
    config_mgr.set_project_config(ProjectConfig(
        name="GeneFusionAI",
        path=str(gf_dir),
        environment_type="conda",
        python_interpreter="/envs/genefusion/bin/python",
    ))
    config_mgr.set_project_config(ProjectConfig(
        name="Clarify",
        path=str(cl_dir),
        environment_type="venv",
    ))

    # 4. Auto-discover and register projects
    discovered_list = discovery.discover_projects()
    assert len(discovered_list) == 2

    auto_records = discovery.auto_register_discovered()
    assert len(auto_records) == 2
    assert registry.has_project("GeneFusionAI") is True
    assert registry.has_project("Clarify") is True

    # 5. Dispatch task to GeneFusionAI
    req_gf = TaskRequest(
        action="inspect_project",
        project_name="GeneFusionAI",
        parameters={"detail_level": "full"},
    )
    res_gf = operator.submit_task(req_gf)
    assert res_gf.status == TaskState.COMPLETED
    assert res_gf.is_success is True

    # 6. Run CoreDiagnostics
    report = diagnostics.run_diagnostics()
    assert report.overall_status == "HEALTHY"
    assert report.failed_count == 0
    assert report.passed_count == 5
