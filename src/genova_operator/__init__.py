"""Genova Operator — Operational and automation layer for Genova Nexus.

Genova Operator acts as the execution layer that converts decision-making
plans into concrete software, experiment, and research operations.
"""

from genova_operator.__version__ import __version__
from genova_operator.activity import (
    ActivityCategory,
    ActivityEntry,
    ProjectActivitySummary,
    ProjectActivityTracker,
)
from genova_operator.config import (
    ConfigManager,
    OperatorConfig,
    ProjectConfig,
)
from genova_operator.core import (
    EventBus,
    GenovaOperator,
    OperatorEvent,
    OperatorStatus,
    TaskRequest,
    TaskResult,
    TaskState,
)
from genova_operator.diagnostics import (
    CheckStatus,
    CoreDiagnostics,
    DiagnosticCheck,
    DiagnosticReport,
)
from genova_operator.discovery import (
    DiscoveredProject,
    ProjectConfidence,
    ProjectDiscovery,
)
from genova_operator.health import (
    HealthStatus,
    ProjectHealthManager,
    ProjectHealthReport,
)
from genova_operator.inspector import (
    ProjectInspectionReport,
    ProjectInspector,
)
from genova_operator.metadata import (
    ProjectMetadata,
    ProjectMetadataManager,
)
from genova_operator.registry import (
    EnvironmentInfo,
    ProjectIdentity,
    ProjectRecord,
    ProjectRegistry,
    RepositoryInfo,
)
from genova_operator.state import (
    ProjectState,
    ProjectStateManager,
    ProjectStateSummary,
    StateTransitionRecord,
)
from genova_operator.workspace import (
    WorkspaceHealth,
    WorkspaceInfo,
    WorkspaceManager,
    WorkspaceStatus,
)

__all__ = [
    "__version__",
    "GenovaOperator",
    "ConfigManager",
    "OperatorConfig",
    "ProjectConfig",
    "WorkspaceManager",
    "WorkspaceInfo",
    "WorkspaceHealth",
    "WorkspaceStatus",
    "ProjectRegistry",
    "ProjectRecord",
    "ProjectIdentity",
    "RepositoryInfo",
    "EnvironmentInfo",
    "ProjectDiscovery",
    "DiscoveredProject",
    "ProjectConfidence",
    "CoreDiagnostics",
    "DiagnosticCheck",
    "DiagnosticReport",
    "CheckStatus",
    "ProjectInspector",
    "ProjectInspectionReport",
    "ProjectMetadataManager",
    "ProjectMetadata",
    "ProjectHealthManager",
    "ProjectHealthReport",
    "HealthStatus",
    "ProjectStateManager",
    "ProjectState",
    "StateTransitionRecord",
    "ProjectStateSummary",
    "ProjectActivityTracker",
    "ActivityEntry",
    "ActivityCategory",
    "ProjectActivitySummary",
    "EventBus",
    "TaskRequest",
    "TaskResult",
    "TaskState",
    "OperatorStatus",
    "OperatorEvent",
]
