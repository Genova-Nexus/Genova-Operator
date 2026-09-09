"""CoreDiagnostics component for Genova Operator.

Validates system health and foundation stability across Core, Config, Workspace,
Registry, and Discovery components.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from genova_operator.config.manager import ConfigManager
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.diagnostics.models import (
    CheckStatus,
    DiagnosticCheck,
    DiagnosticReport,
)
from genova_operator.discovery.manager import ProjectDiscovery
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class CoreDiagnostics(BaseComponent):
    """Core Diagnostics component for Genova Operator.

    Validates foundation health across all Phase 1 components.
    """

    def __init__(
        self,
        name: str = "core-diagnostics",
        operator: Optional[GenovaOperator] = None,
    ) -> None:
        self._name = name
        self._operator = operator
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize CoreDiagnostics."""
        logger.info("Initializing CoreDiagnostics (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("CoreDiagnostics initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown CoreDiagnostics."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def run_diagnostics(
        self,
        operator: Optional[GenovaOperator] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
        project_registry: Optional[ProjectRegistry] = None,
        config_manager: Optional[ConfigManager] = None,
        project_discovery: Optional[ProjectDiscovery] = None,
    ) -> DiagnosticReport:
        """Run complete foundation diagnostics across all components.

        Args:
            operator: Optional target GenovaOperator instance.
            workspace_manager: Optional target WorkspaceManager.
            project_registry: Optional target ProjectRegistry.
            config_manager: Optional target ConfigManager.
            project_discovery: Optional target ProjectDiscovery.

        Returns:
            DiagnosticReport containing results for all foundation checks.
        """
        target_operator = operator or self._operator
        report = DiagnosticReport()

        logger.info("Starting Genova Operator Core Diagnostics...")

        # Check 1: Core Operator Orchestrator
        report.checks.append(self.check_core(target_operator))

        # Check 2: Config Manager
        report.checks.append(self.check_config(target_operator, config_manager))

        # Check 3: Workspace Manager
        report.checks.append(self.check_workspace(target_operator, workspace_manager))

        # Check 4: Project Registry
        report.checks.append(self.check_registry(target_operator, project_registry))

        # Check 5: Project Discovery
        report.checks.append(self.check_discovery(target_operator, project_discovery))

        logger.info(
            "Diagnostics completed. Overall status: %s (%d passed, %d warning, %d failed).",
            report.overall_status,
            report.passed_count,
            report.warning_count,
            report.failed_count,
        )
        return report

    def check_core(self, operator: Optional[GenovaOperator]) -> DiagnosticCheck:
        """Check GenovaOperator orchestrator and EventBus."""
        start = time.time()
        if operator is None:
            return DiagnosticCheck(
                name="Core Orchestrator Status",
                category="core",
                status=CheckStatus.WARNING,
                message="No GenovaOperator instance provided to diagnostics.",
                duration=time.time() - start,
            )

        status_val = operator.status.value
        is_ready = operator.status == OperatorStatus.READY
        check_status = CheckStatus.PASSED if is_ready else CheckStatus.FAILED
        msg = f"GenovaOperator status is '{status_val}'."

        return DiagnosticCheck(
            name="Core Orchestrator Status",
            category="core",
            status=check_status,
            message=msg,
            details=operator.get_status_report(),
            duration=time.time() - start,
        )

    def check_config(
        self,
        operator: Optional[GenovaOperator],
        config_mgr: Optional[ConfigManager],
    ) -> DiagnosticCheck:
        """Check ConfigManager component."""
        start = time.time()
        mgr = config_mgr
        if mgr is None and operator is not None and operator.has_component("operator-config"):
            mgr = operator.get_component("operator-config")  # type: ignore

        if mgr is None:
            return DiagnosticCheck(
                name="Configuration Subsystem",
                category="config",
                status=CheckStatus.WARNING,
                message="ConfigManager component not registered.",
                duration=time.time() - start,
            )

        is_ready = mgr.get_status() == OperatorStatus.READY
        status = CheckStatus.PASSED if is_ready else CheckStatus.FAILED
        return DiagnosticCheck(
            name="Configuration Subsystem",
            category="config",
            status=status,
            message=f"ConfigManager status is '{mgr.get_status().value}'.",
            details=mgr.config.to_dict(),
            duration=time.time() - start,
        )

    def check_workspace(
        self,
        operator: Optional[GenovaOperator],
        workspace_mgr: Optional[WorkspaceManager],
    ) -> DiagnosticCheck:
        """Check WorkspaceManager component."""
        start = time.time()
        mgr = workspace_mgr
        if mgr is None and operator is not None and operator.has_component("workspace-manager"):
            mgr = operator.get_component("workspace-manager")  # type: ignore

        if mgr is None:
            return DiagnosticCheck(
                name="Workspace Subsystem",
                category="workspace",
                status=CheckStatus.WARNING,
                message="WorkspaceManager component not registered.",
                duration=time.time() - start,
            )

        health = mgr.check_health()
        status = CheckStatus.PASSED if health.is_healthy else CheckStatus.FAILED
        return DiagnosticCheck(
            name="Workspace Subsystem",
            category="workspace",
            status=status,
            message=health.message,
            details=health.to_dict(),
            duration=time.time() - start,
        )

    def check_registry(
        self,
        operator: Optional[GenovaOperator],
        registry_mgr: Optional[ProjectRegistry],
    ) -> DiagnosticCheck:
        """Check ProjectRegistry component."""
        start = time.time()
        mgr = registry_mgr
        if mgr is None and operator is not None and operator.has_component("project-registry"):
            mgr = operator.get_component("project-registry")  # type: ignore

        if mgr is None:
            return DiagnosticCheck(
                name="Project Registry Subsystem",
                category="registry",
                status=CheckStatus.WARNING,
                message="ProjectRegistry component not registered.",
                duration=time.time() - start,
            )

        is_ready = mgr.get_status() == OperatorStatus.READY
        status = CheckStatus.PASSED if is_ready else CheckStatus.FAILED
        return DiagnosticCheck(
            name="Project Registry Subsystem",
            category="registry",
            status=status,
            message=f"ProjectRegistry is '{mgr.get_status().value}' with {mgr.count()} projects registered.",
            details={"projects_count": mgr.count(), "projects": list(mgr.list_projects().keys())},
            duration=time.time() - start,
        )

    def check_discovery(
        self,
        operator: Optional[GenovaOperator],
        discovery_mgr: Optional[ProjectDiscovery],
    ) -> DiagnosticCheck:
        """Check ProjectDiscovery component."""
        start = time.time()
        mgr = discovery_mgr
        if mgr is None and operator is not None and operator.has_component("project-discovery"):
            mgr = operator.get_component("project-discovery")  # type: ignore

        if mgr is None:
            return DiagnosticCheck(
                name="Project Discovery Subsystem",
                category="discovery",
                status=CheckStatus.WARNING,
                message="ProjectDiscovery component not registered.",
                duration=time.time() - start,
            )

        is_ready = mgr.get_status() == OperatorStatus.READY
        status = CheckStatus.PASSED if is_ready else CheckStatus.FAILED
        return DiagnosticCheck(
            name="Project Discovery Subsystem",
            category="discovery",
            status=status,
            message=f"ProjectDiscovery is '{mgr.get_status().value}'.",
            duration=time.time() - start,
        )
