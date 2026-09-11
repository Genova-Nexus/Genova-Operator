"""ProjectHealthManager component for Genova Operator.

Evaluates 5-pillar health assessments for registered projects:
1. Existence & Accessibility
2. Configuration Validity
3. Runtime Environment Availability
4. Dependencies Accessibility
5. Structural Integrity & Component Presence
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from genova_operator.config.manager import ConfigManager
from genova_operator.core.exceptions import GenovaOperatorError, ProjectNotFoundError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.diagnostics.models import CheckStatus
from genova_operator.health.models import (
    HealthCheckItem,
    HealthStatus,
    ProjectHealthReport,
)
from genova_operator.inspector.manager import ProjectInspector
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import ProjectRecord
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class ProjectHealthManager(BaseComponent):
    """Project Health Manager component for Genova Operator.

    Assesses health of target projects and computes operational readiness scores.
    """

    def __init__(
        self,
        name: str = "project-health",
        project_registry: Optional[ProjectRegistry] = None,
        project_inspector: Optional[ProjectInspector] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
        config_manager: Optional[ConfigManager] = None,
    ) -> None:
        self._name = name
        self._project_registry = project_registry
        self._project_inspector = project_inspector
        self._workspace_manager = workspace_manager
        self._config_manager = config_manager
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize the ProjectHealthManager component."""
        logger.info("Initializing ProjectHealthManager (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("ProjectHealthManager initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectHealthManager."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def assess_project_health(
        self,
        target: Union[str, ProjectRecord, Path],
    ) -> ProjectHealthReport:
        """Assess complete 5-pillar health for a target project.

        Args:
            target: Project name, ProjectRecord, or directory Path.

        Returns:
            ProjectHealthReport instance.
        """
        project_name, project_path, record = self._resolve_target(target)
        abs_path = Path(project_path).resolve()

        logger.info("Assessing project health for '%s' (%s)...", project_name, abs_path)
        start_time = time.time()

        checks: List[HealthCheckItem] = []
        issues: List[str] = []
        recommendations: List[str] = []

        # Pillar 1: Existence & Accessibility
        check_exist = self.check_existence(abs_path)
        checks.append(check_exist)
        if check_exist.status == CheckStatus.FAILED:
            issues.append(f"Directory Error: {check_exist.message}")
            recommendations.append("Ensure the project root directory exists and has read/write permissions.")

            return ProjectHealthReport(
                project_name=project_name,
                project_path=str(abs_path),
                status=HealthStatus.UNAVAILABLE,
                health_score=0.0,
                checks=checks,
                issues=issues,
                recommendations=recommendations,
                assessed_at=time.time(),
            )

        # Pillar 2: Configuration Validity
        check_config = self.check_configuration(abs_path, record=record)
        checks.append(check_config)
        if check_config.status != CheckStatus.PASSED:
            issues.append(f"Config Warning: {check_config.message}")
            recommendations.append("Verify project configuration file (genova_project.json or pyproject.toml).")

        # Pillar 3: Runtime Environment Availability
        check_env = self.check_environment(abs_path, record=record)
        checks.append(check_env)
        if check_env.status != CheckStatus.PASSED:
            issues.append(f"Environment Notice: {check_env.message}")
            recommendations.append("Configure valid Python interpreter and environment in ProjectRegistry/Config.")

        # Pillar 4: Dependencies Accessibility
        check_deps = self.check_dependencies(abs_path)
        checks.append(check_deps)
        if check_deps.status != CheckStatus.PASSED:
            issues.append(f"Dependency Issue: {check_deps.message}")
            recommendations.append("Install missing project dependencies listed in requirements.txt or pyproject.toml.")

        # Pillar 5: Structural Integrity & Component Presence
        check_struct = self.check_structure(abs_path)
        checks.append(check_struct)
        if check_struct.status != CheckStatus.PASSED:
            issues.append(f"Structure Notice: {check_struct.message}")
            recommendations.append("Ensure main entry script (main.py/app.py/train.py) and test suite exist.")

        # Calculate Score and Status
        health_score, overall_status = self._calculate_health(checks)

        report = ProjectHealthReport(
            project_name=project_name,
            project_path=str(abs_path),
            status=overall_status,
            health_score=health_score,
            checks=checks,
            issues=issues,
            recommendations=recommendations,
            assessed_at=time.time(),
        )

        logger.info(
            "Health assessment completed for '%s': Status %s, Score %.1f%% in %.3fs.",
            project_name,
            overall_status.value,
            health_score,
            time.time() - start_time,
        )
        return report

    def assess_all_projects(self) -> Dict[str, ProjectHealthReport]:
        """Assess health for all registered projects in ProjectRegistry."""
        if not self._project_registry:
            raise GenovaOperatorError("Cannot assess all projects. No ProjectRegistry connected.")

        reports: Dict[str, ProjectHealthReport] = {}
        for name, record in self._project_registry.list_projects().items():
            reports[name] = self.assess_project_health(record)
        return reports

    def check_existence(self, path: Path) -> HealthCheckItem:
        """Pillar 1: Check project directory existence and permissions."""
        if not path.exists():
            return HealthCheckItem(
                name="Project Existence",
                category="existence",
                status=CheckStatus.FAILED,
                message=f"Path '{path}' does not exist.",
                weight=2.0,
            )
        if not path.is_dir():
            return HealthCheckItem(
                name="Project Directory Check",
                category="existence",
                status=CheckStatus.FAILED,
                message=f"Path '{path}' is a file, not a directory.",
                weight=2.0,
            )
        if not os.access(path, os.R_OK):
            return HealthCheckItem(
                name="Project Read Permissions",
                category="existence",
                status=CheckStatus.FAILED,
                message=f"Path '{path}' is not readable.",
                weight=2.0,
            )

        return HealthCheckItem(
            name="Project Existence & Accessibility",
            category="existence",
            status=CheckStatus.PASSED,
            message=f"Project root directory '{path.name}' exists and is accessible.",
            weight=2.0,
        )

    def check_configuration(self, path: Path, record: Optional[ProjectRecord]) -> HealthCheckItem:
        """Pillar 2: Check project configuration validity."""
        marker1 = path / "genova_project.json"
        marker2 = path / ".genova" / "project.json"
        pyproject = path / "pyproject.toml"

        if marker1.is_file() or marker2.is_file() or pyproject.is_file() or record is not None:
            return HealthCheckItem(
                name="Configuration Validity",
                category="config",
                status=CheckStatus.PASSED,
                message="Valid project configuration detected.",
                weight=1.0,
            )

        return HealthCheckItem(
            name="Configuration Validity",
            category="config",
            status=CheckStatus.WARNING,
            message="No explicit genova_project.json or pyproject.toml config file detected.",
            weight=1.0,
        )

    def check_environment(self, path: Path, record: Optional[ProjectRecord]) -> HealthCheckItem:
        """Pillar 3: Check runtime environment availability."""
        interpreter = record.environment.python_interpreter if record and record.environment else sys.executable
        interp_path = Path(interpreter) if interpreter else Path(sys.executable)

        if interp_path.exists():
            return HealthCheckItem(
                name="Runtime Environment",
                category="environment",
                status=CheckStatus.PASSED,
                message=f"Python interpreter available at '{interp_path}'.",
                weight=1.5,
                details={"interpreter": str(interp_path)},
            )

        return HealthCheckItem(
            name="Runtime Environment",
            category="environment",
            status=CheckStatus.WARNING,
            message=f"Configured interpreter '{interp_path}' not found. Falling back to system default.",
            weight=1.5,
        )

    def check_dependencies(self, path: Path) -> HealthCheckItem:
        """Pillar 4: Check dependency files accessibility."""
        req_file = path / "requirements.txt"
        pyproject = path / "pyproject.toml"

        if req_file.is_file() or pyproject.is_file():
            return HealthCheckItem(
                name="Dependencies Accessibility",
                category="dependencies",
                status=CheckStatus.PASSED,
                message="Project dependency specifications are accessible.",
                weight=1.0,
            )

        return HealthCheckItem(
            name="Dependencies Accessibility",
            category="dependencies",
            status=CheckStatus.WARNING,
            message="No requirements.txt or pyproject.toml dependency specification file found.",
            weight=1.0,
        )

    def check_structure(self, path: Path) -> HealthCheckItem:
        """Pillar 5: Check structural component presence."""
        entry_found = any((path / f).is_file() for f in ("main.py", "app.py", "train.py", "run.py")) or (path / "src").is_dir()
        has_tests = (path / "tests").is_dir()

        if entry_found and has_tests:
            return HealthCheckItem(
                name="Structural Component Integrity",
                category="structure",
                status=CheckStatus.PASSED,
                message="Entry points and test suite components are present.",
                weight=1.0,
            )
        elif entry_found:
            return HealthCheckItem(
                name="Structural Component Integrity",
                category="structure",
                status=CheckStatus.PASSED,
                message="Entry points present.",
                weight=1.0,
            )
        else:
            return HealthCheckItem(
                name="Structural Component Integrity",
                category="structure",
                status=CheckStatus.WARNING,
                message="No standard entry points (main.py/app.py/train.py) or src/ directory found.",
                weight=1.0,
            )

    def _calculate_health(self, checks: List[HealthCheckItem]) -> Tuple[float, HealthStatus]:
        """Calculate score percentage and overall HealthStatus."""
        if not checks:
            return 0.0, HealthStatus.UNAVAILABLE

        total_weight = sum(c.weight for c in checks)
        passed_weight = sum(c.weight for c in checks if c.status == CheckStatus.PASSED)
        warning_weight = sum(c.weight * 0.5 for c in checks if c.status == CheckStatus.WARNING)

        score = ((passed_weight + warning_weight) / total_weight) * 100.0

        if any(c.status == CheckStatus.FAILED for c in checks):
            status = HealthStatus.UNHEALTHY
        elif score >= 90.0:
            status = HealthStatus.HEALTHY
        elif score >= 60.0:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return score, status

    def _resolve_target(
        self,
        target: Union[str, ProjectRecord, Path],
    ) -> Tuple[str, str, Optional[ProjectRecord]]:
        """Resolve project name, path, and optional record."""
        if isinstance(target, ProjectRecord):
            return target.name, target.path, target

        if isinstance(target, Path):
            return target.name, str(target), None

        if isinstance(target, str):
            if self._project_registry and self._project_registry.has_project(target):
                record = self._project_registry.get_project(target)
                if record:
                    return record.name, record.path, record

            p_path = Path(target)
            return p_path.name, str(p_path), None

        raise GenovaOperatorError(f"Unsupported target type for health assessment: {type(target)}")
