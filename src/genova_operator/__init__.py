"""Genova Operator — Operational and automation layer for Genova Nexus.

Genova Operator acts as the execution layer that converts decision-making
plans into concrete software, experiment, and research operations.
"""

from genova_operator.__version__ import __version__
from genova_operator.core import (
    EventBus,
    GenovaOperator,
    OperatorEvent,
    OperatorStatus,
    TaskRequest,
    TaskResult,
    TaskState,
)

__all__ = [
    "__version__",
    "GenovaOperator",
    "EventBus",
    "TaskRequest",
    "TaskResult",
    "TaskState",
    "OperatorStatus",
    "OperatorEvent",
]
