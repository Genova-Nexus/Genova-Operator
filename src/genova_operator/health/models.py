"""Project Health models for Genova Operator.

Defines health status enums, check items, and comprehensive ProjectHealthReport
objects used to evaluate operational readiness of projects like GeneFusionAI and Clarify.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from genova_operator.diagnostics.models import CheckStatus


class HealthStatus(Enum):
    """Overall health status of a project."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class HealthCheckItem:
    """Individual health assessment check item.

    Attributes:
        name: Short name of the health check.
        category: Pillar category ('existence', 'config', 'environment', 'dependencies', 'structure').
        status: CheckStatus enum (PASSED, WARNING, FAILED).
        message: Status message describing the check output.
        weight: Relative weight factor for score calculation (default 1.0).
        details: Additional diagnostic detail dictionary.
    """
    name: str
    category: str
    status: CheckStatus = CheckStatus.PASSED
    message: str = ""
    weight: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "message": self.message,
            "weight": self.weight,
            "details": self.details,
        }


@dataclass
class ProjectHealthReport:
    """Comprehensive health report for a target project.

    Aggregates overall health status, numerical health score percentage (0–100%),
    check items, detected issues, and actionable recommendations.
    """
    project_name: str
    project_path: str
    status: HealthStatus = HealthStatus.HEALTHY
    health_score: float = 100.0
    checks: List[HealthCheckItem] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: float = field(default_factory=time.time)

    @property
    def is_healthy(self) -> bool:
        """Return True if status is HEALTHY."""
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_path": self.project_path,
            "status": self.status.value,
            "health_score": round(self.health_score, 1),
            "is_healthy": self.is_healthy,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "checks": [c.to_dict() for c in self.checks],
            "assessed_at": self.assessed_at,
        }
