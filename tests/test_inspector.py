"""Unit tests for Genova Operator Project Inspector."""

import pytest
from pathlib import Path

from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.inspector.manager import ProjectInspector
from genova_operator.inspector.models import ProjectInspectionReport
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.workspace.manager import WorkspaceManager


def test_directory_tree_building(tmp_path: Path) -> None:
    """Test building directory tree hierarchy."""
    proj_dir = tmp_path / "GeneFusionAI"
    proj_dir.mkdir()
    (proj_dir / "file1.txt").write_text("content1")
    (proj_dir / "src").mkdir()
    (proj_dir / "src" / "main.py").write_text("print('hello')")

    inspector = ProjectInspector()
    tree = inspector.inspect_directory_tree(proj_dir, max_depth=2)

    assert tree.root_name == "GeneFusionAI"
    assert tree.total_files == 2
    assert tree.total_directories == 2
    assert tree.root_node is not None
    assert len(tree.root_node.children) == 2


def test_dependency_extraction(tmp_path: Path) -> None:
    """Test parsing dependencies from requirements.txt and pyproject.toml."""
    proj_dir = tmp_path / "Clarify"
    proj_dir.mkdir()

    req_file = proj_dir / "requirements.txt"
    req_file.write_text("torch>=2.0.0\npytest\nrequests==2.28.1\n# comment\n")

    pyproj_file = proj_dir / "pyproject.toml"
    pyproj_file.write_text('[project]\ndependencies = ["pandas", "numpy"]\n')

    inspector = ProjectInspector()
    deps_summary = inspector.inspect_dependencies(proj_dir)

    assert len(deps_summary.package_files_found) == 2
    assert "torch" in deps_summary.dependencies
    assert "pytest" in deps_summary.dependencies
    assert "torch" in deps_summary.frameworks
    assert "pytest" in deps_summary.frameworks


def test_full_project_inspection(tmp_path: Path) -> None:
    """Test running full project inspection on sample GeneFusionAI directory."""
    gf_dir = tmp_path / "GeneFusionAI"
    gf_dir.mkdir()
    (gf_dir / "requirements.txt").write_text("torch\n")
    (gf_dir / "main.py").write_text("print('train')")
    (gf_dir / "tests").mkdir()
    (gf_dir / "tests" / "test_model.py").write_text("def test(): pass")

    registry = ProjectRegistry()
    registry.register_project("GeneFusionAI", str(gf_dir))

    inspector = ProjectInspector(project_registry=registry)
    report = inspector.inspect_project("GeneFusionAI")

    assert isinstance(report, ProjectInspectionReport)
    assert report.project_name == "GeneFusionAI"
    assert report.project_path == str(gf_dir.resolve())
    assert report.entry_points.entry_scripts.get("main") == "main.py"
    assert report.entry_points.has_tests is True
    assert "torch" in report.dependencies.dependencies
    assert report.metadata["registered"] is True

    # Check dict conversion
    data = report.to_dict()
    assert data["project_name"] == "GeneFusionAI"
    assert "directory_tree" in data
    assert "dependencies" in data


def test_project_inspector_component_integration() -> None:
    """Test registering ProjectInspector with GenovaOperator core."""
    operator = GenovaOperator()
    inspector = ProjectInspector()

    operator.register_component(inspector)
    operator.initialize()

    assert operator.has_component("project-inspector")
    retrieved = operator.get_component("project-inspector")
    assert isinstance(retrieved, ProjectInspector)
    assert retrieved.get_status() == OperatorStatus.READY
