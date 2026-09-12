"""Genova Operator Project State Package (`Project State`).

Provides standardized project state tracking (AVAILABLE, ACTIVE, INACTIVE, RUNNING,
UNHEALTHY, UNAVAILABLE), active task coupling, and transition history.
"""

from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import (
    ProjectState,
    ProjectStateSummary,
    StateTransitionRecord,
)

__all__ = [
    "ProjectStateManager",
    "ProjectState",
    "StateTransitionRecord",
    "ProjectStateSummary",
]
