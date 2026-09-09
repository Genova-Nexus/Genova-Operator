"""Core Diagnostics models for Genova Operator.

Defines check status enums, diagnostic checks, and diagnostic report models used
to validate system foundation health.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckStatus(Enum):
    """Status of an individual diagnostic check."""
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


@dataclass
class DiagnosticCheck:
    """Result of an individual system diagnostic check.

    Attributes:
        name: Short descriptive name of the check.
        category: Component or module category being tested.
        status: CheckStatus enum (PASSED, WARNING, FAILED).
        message: Human-readable status message.
        details: Additional diagnostic detail dictionary.
        duration: Execution duration in seconds.
    """
    name: str
    category: str
    status: CheckStatus = CheckStatus.PASSED
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration": self.duration,
        }


@dataclass
class DiagnosticReport:
    """Comprehensive foundation diagnostic report for Genova Operator.

    Attributes:
        checks: List of completed DiagnosticCheck instances.
        timestamp: Epoch timestamp when diagnostics were executed.
    """
    checks: List[DiagnosticCheck] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASSED)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.WARNING)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAILED)

    @property
    def overall_status(self) -> str:
        """Return overall health status ('HEALTHY', 'DEGRADED', or 'UNHEALTHY')."""
        if self.failed_count > 0:
            return "UNHEALTHY"
        elif self.warning_count > 0:
            return "DEGRADED"
        return "HEALTHY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "total_checks": self.total_checks,
            "passed_count": self.passed_count,
            "warning_count": self.warning_count,
            "failed_count": self.failed_count,
            "timestamp": self.timestamp,
            "checks": [c.to_dict() for c in self.checks],
        }
