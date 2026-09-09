"""Genova Operator Core Diagnostics Package (`Core Diagnostics`).

Provides system health validation, component readiness checks, and diagnostic
reports for the Genova Operator foundation.
"""

from genova_operator.diagnostics.manager import CoreDiagnostics
from genova_operator.diagnostics.models import (
    CheckStatus,
    DiagnosticCheck,
    DiagnosticReport,
)

__all__ = [
    "CoreDiagnostics",
    "DiagnosticReport",
    "DiagnosticCheck",
    "CheckStatus",
]
