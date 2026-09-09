"""Unit tests for Genova Operator Core Diagnostics."""

import pytest
from pathlib import Path

from genova_operator.config.manager import ConfigManager
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.diagnostics.manager import CoreDiagnostics
from genova_operator.diagnostics.models import CheckStatus, DiagnosticCheck, DiagnosticReport
from genova_operator.discovery.manager import ProjectDiscovery
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.workspace.manager import WorkspaceManager


def test_diagnostic_models_serialization() -> None:
    """Test DiagnosticCheck and DiagnosticReport serialization."""
    check1 = DiagnosticCheck(
        name="Test Check 1",
        category="core",
        status=CheckStatus.PASSED,
        message="All ok",
    )
    check2 = DiagnosticCheck(
        name="Test Check 2",
        category="workspace",
        status=CheckStatus.WARNING,
        message="Minor warning",
    )

    report = DiagnosticReport(checks=[check1, check2])
    assert report.total_checks == 2
    assert report.passed_count == 1
    assert report.warning_count == 1
    assert report.failed_count == 0
    assert report.overall_status == "DEGRADED"

    data = report.to_dict()
    assert data["overall_status"] == "DEGRADED"
    assert data["total_checks"] == 2


def test_core_diagnostics_execution(tmp_path: Path) -> None:
    """Test running CoreDiagnostics across registered components."""
    operator = GenovaOperator()
    config_mgr = ConfigManager()
    ws_mgr = WorkspaceManager(root_path=tmp_path)
    registry = ProjectRegistry()
    discovery = ProjectDiscovery(workspace_manager=ws_mgr, project_registry=registry)
    diagnostics = CoreDiagnostics(operator=operator)

    operator.register_component(config_mgr)
    operator.register_component(ws_mgr)
    operator.register_component(registry)
    operator.register_component(discovery)
    operator.register_component(diagnostics)

    operator.initialize()

    report = diagnostics.run_diagnostics()

    assert report.overall_status == "HEALTHY"
    assert report.total_checks == 5
    assert report.failed_count == 0
    assert report.passed_count == 5
