"""Unit tests for Genova Operator Project Discovery."""

import json
import pytest
from pathlib import Path

from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.discovery.manager import ProjectDiscovery
from genova_operator.discovery.models import ProjectConfidence
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.workspace.manager import WorkspaceManager


def test_explicit_genova_project_detection(tmp_path: Path) -> None:
    """Test detecting explicit Genova projects with genova_project.json or .genova/project.json."""
    project_dir = tmp_path / "GeneFusionAI"
    project_dir.mkdir(parents=True)

    marker = project_dir / "genova_project.json"
    with open(marker, "w", encoding="utf-8") as f:
        json.dump({"name": "GeneFusionAI", "type": "ml_research"}, f)

    discovery = ProjectDiscovery()
    discovered = discovery.inspect_directory(project_dir)

    assert discovered.name == "GeneFusionAI"
    assert discovered.confidence == ProjectConfidence.HIGH
    assert "explicit_genova_marker" in discovered.matched_rules
    assert discovered.project_type == "ml_research"


def test_python_project_detection(tmp_path: Path) -> None:
    """Test detecting standard Python projects with pyproject.toml or requirements.txt."""
    project_dir = tmp_path / "Clarify"
    project_dir.mkdir(parents=True)

    (project_dir / "pyproject.toml").touch()
    (project_dir / "requirements.txt").touch()
    (project_dir / "src").mkdir()
    (project_dir / "main.py").touch()

    discovery = ProjectDiscovery()
    discovered = discovery.inspect_directory(project_dir)

    assert discovered.name == "Clarify"
    assert discovered.confidence == ProjectConfidence.HIGH
    assert "pyproject_toml" in discovered.matched_rules
    assert "requirements_txt" in discovered.matched_rules
    assert "src_directory" in discovered.matched_rules
    assert "main" in discovered.detected_entry_points


def test_ordinary_directory_filtering(tmp_path: Path) -> None:
    """Test that plain empty folders or hidden folders return NOT_A_PROJECT."""
    plain_dir = tmp_path / "plain_folder"
    plain_dir.mkdir(parents=True)

    hidden_dir = tmp_path / ".git"
    hidden_dir.mkdir(parents=True)

    discovery = ProjectDiscovery()

    disc_plain = discovery.inspect_directory(plain_dir)
    assert disc_plain.confidence == ProjectConfidence.NOT_A_PROJECT

    disc_hidden = discovery.inspect_directory(hidden_dir)
    assert disc_hidden.confidence == ProjectConfidence.NOT_A_PROJECT


def test_workspace_scanning_and_auto_registration(tmp_path: Path) -> None:
    """Test scanning a workspace projects directory and auto-registering into ProjectRegistry."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True)

    gf_dir = projects_dir / "GeneFusionAI"
    gf_dir.mkdir()
    (gf_dir / "pyproject.toml").touch()

    cl_dir = projects_dir / "Clarify"
    cl_dir.mkdir()
    (cl_dir / "requirements.txt").touch()

    (projects_dir / "random_notes").mkdir()  # plain folder, score 0.0

    ws_mgr = WorkspaceManager(root_path=tmp_path, projects_dir="projects")
    registry = ProjectRegistry()
    discovery = ProjectDiscovery(workspace_manager=ws_mgr, project_registry=registry)

    # Discover projects
    found = discovery.discover_projects(min_confidence=ProjectConfidence.MEDIUM)
    assert len(found) == 2
    names = [p.name for p in found]
    assert "GeneFusionAI" in names
    assert "Clarify" in names

    # Auto-register
    records = discovery.auto_register_discovered(registry=registry)
    assert len(records) == 2
    assert registry.has_project("GeneFusionAI") is True
    assert registry.has_project("Clarify") is True


def test_project_discovery_component_integration() -> None:
    """Test registering ProjectDiscovery with GenovaOperator core."""
    operator = GenovaOperator()
    discovery = ProjectDiscovery()

    operator.register_component(discovery)
    operator.initialize()

    assert operator.has_component("project-discovery")
    retrieved = operator.get_component("project-discovery")
    assert isinstance(retrieved, ProjectDiscovery)
    assert retrieved.get_status() == OperatorStatus.READY
