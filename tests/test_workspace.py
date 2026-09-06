"""Unit tests for Genova Operator Workspace Manager."""

import pytest
from pathlib import Path

from genova_operator.config.manager import ConfigManager
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.workspace.manager import (
    WorkspaceBoundaryError,
    WorkspaceManager,
)
from genova_operator.workspace.models import WorkspaceStatus


def test_workspace_manager_instantiation_and_init(tmp_path: Path) -> None:
    """Test standard WorkspaceManager setup and initialization."""
    ws = WorkspaceManager(root_path=tmp_path, projects_dir="projects")
    assert ws.root_path == tmp_path.resolve()
    assert ws.projects_path == (tmp_path / "projects").resolve()

    ws.initialize()
    assert ws.get_status() == OperatorStatus.READY

    info = ws.get_info()
    assert info.absolute_root_path == str(tmp_path.resolve())
    assert info.status == WorkspaceStatus.ACTIVE


def test_workspace_health_checks(tmp_path: Path) -> None:
    """Test health diagnostics report."""
    ws = WorkspaceManager(root_path=tmp_path)
    health = ws.check_health()
    assert health.exists is True
    assert health.is_directory is True
    assert health.writable is True
    assert health.is_healthy is True

    # Test non-existent path
    non_existent = tmp_path / "does_not_exist"
    ws_bad = WorkspaceManager(root_path=non_existent)
    bad_health = ws_bad.check_health()
    assert bad_health.exists is False
    assert bad_health.is_healthy is False


def test_path_resolution_and_boundary_enforcement(tmp_path: Path) -> None:
    """Test resolving relative paths and raising WorkspaceBoundaryError for outside paths."""
    ws = WorkspaceManager(root_path=tmp_path)
    ws.initialize()

    # Valid inside path
    inside = ws.resolve_path("projects/GeneFusionAI")
    assert inside == (tmp_path / "projects" / "GeneFusionAI").resolve()

    # Boundary violation
    outside_path = tmp_path.parent / "secret_file.txt"
    with pytest.raises(WorkspaceBoundaryError):
        ws.resolve_path(outside_path, enforce_boundary=True)

    # Allowed when boundary enforcement is False
    bypassed = ws.resolve_path(outside_path, enforce_boundary=False)
    assert bypassed == outside_path.resolve()


def test_find_candidate_project_directories(tmp_path: Path) -> None:
    """Test scanning projects folder for candidate project subdirectories."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    (projects_dir / "GeneFusionAI").mkdir()
    (projects_dir / "Clarify").mkdir()
    (projects_dir / ".hidden_dir").mkdir()  # should be ignored
    (projects_dir / "file.txt").touch()      # should be ignored

    ws = WorkspaceManager(root_path=tmp_path, projects_dir="projects")
    candidates = ws.find_candidate_project_dirs()

    assert candidates == ["Clarify", "GeneFusionAI"]


def test_workspace_marker_creation(tmp_path: Path) -> None:
    """Test creation and detection of workspace marker file."""
    ws = WorkspaceManager(root_path=tmp_path)
    assert ws.has_marker() is False

    marker_file = ws.create_marker(metadata={"env": "test"})
    assert marker_file.is_file()
    assert ws.has_marker() is True


def test_workspace_manager_component_integration(tmp_path: Path) -> None:
    """Test integrating WorkspaceManager into GenovaOperator core."""
    operator = GenovaOperator()
    config_mgr = ConfigManager()
    config_mgr.config.workspace.root_path = str(tmp_path)

    ws_mgr = WorkspaceManager(config_manager=config_mgr)
    operator.register_component(config_mgr)
    operator.register_component(ws_mgr)

    operator.initialize()

    assert operator.has_component("workspace-manager")
    retrieved_ws = operator.get_component("workspace-manager")
    assert isinstance(retrieved_ws, WorkspaceManager)
    assert retrieved_ws.root_path == tmp_path.resolve()
