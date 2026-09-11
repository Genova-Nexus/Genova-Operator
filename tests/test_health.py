"""Unit tests for Genova Operator Project Health."""

import json
import pytest
from pathlib import Path

from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.health.manager import ProjectHealthManager
from genova_operator.health.models import HealthStatus, ProjectHealthReport
from genova_operator.registry.manager import ProjectRegistry


def test_healthy_project_assessment(tmp_path: Path) -> None:
    """Test health assessment on a healthy sample GeneFusionAI directory."""
    gf_dir = tmp_path / "GeneFusionAI"
    gf_dir.mkdir()
    with open(gf_dir / "genova_project.json", "w", encoding="utf-8") as f:
        json.dump({"name": "GeneFusionAI", "type": "ml_research"}, f)
    (gf_dir / "requirements.txt").write_text("torch\n")
    (gf_dir / "main.py").write_text("print('start')")
    (gf_dir / "tests").mkdir()

    health_mgr = ProjectHealthManager()
    report = health_mgr.assess_project_health(gf_dir)

    assert isinstance(report, ProjectHealthReport)
    assert report.status == HealthStatus.HEALTHY
    assert report.health_score == 100.0
    assert report.is_healthy is True
    assert len(report.issues) == 0


def test_unhealthy_nonexistent_project(tmp_path: Path) -> None:
    """Test health assessment on non-existent directory."""
    non_existent = tmp_path / "does_not_exist"
    health_mgr = ProjectHealthManager()
    report = health_mgr.assess_project_health(non_existent)

    assert report.status == HealthStatus.UNAVAILABLE
    assert report.health_score == 0.0
    assert report.is_healthy is False
    assert len(report.issues) > 0


def test_degraded_project_assessment(tmp_path: Path) -> None:
    """Test health assessment on directory missing config and requirements."""
    bare_dir = tmp_path / "BareProject"
    bare_dir.mkdir()

    health_mgr = ProjectHealthManager()
    report = health_mgr.assess_project_health(bare_dir)

    assert report.status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)
    assert report.health_score < 100.0
    assert len(report.recommendations) > 0


def test_assess_all_projects(tmp_path: Path) -> None:
    """Test assessing all projects registered in ProjectRegistry."""
    gf_dir = tmp_path / "GeneFusionAI"
    gf_dir.mkdir()
    (gf_dir / "genova_project.json").touch()

    cl_dir = tmp_path / "Clarify"
    cl_dir.mkdir()
    (cl_dir / "pyproject.toml").touch()

    registry = ProjectRegistry()
    registry.register_project("GeneFusionAI", str(gf_dir))
    registry.register_project("Clarify", str(cl_dir))

    health_mgr = ProjectHealthManager(project_registry=registry)
    all_reports = health_mgr.assess_all_projects()

    assert len(all_reports) == 2
    assert "GeneFusionAI" in all_reports
    assert "Clarify" in all_reports


def test_project_health_component_integration() -> None:
    """Test registering ProjectHealthManager with GenovaOperator core."""
    operator = GenovaOperator()
    health_mgr = ProjectHealthManager()

    operator.register_component(health_mgr)
    operator.initialize()

    assert operator.has_component("project-health")
    retrieved = operator.get_component("project-health")
    assert isinstance(retrieved, ProjectHealthManager)
    assert retrieved.get_status() == OperatorStatus.READY
