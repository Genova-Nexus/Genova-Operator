"""Genova Operator Project Registry Package (`Project Registry`).

Provides central project identity management, repository and environment details,
record persistence, and registration lookup for Genova projects.
"""

from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import (
    EnvironmentInfo,
    ProjectIdentity,
    ProjectRecord,
    RepositoryInfo,
)

__all__ = [
    "ProjectRegistry",
    "ProjectRecord",
    "ProjectIdentity",
    "RepositoryInfo",
    "EnvironmentInfo",
]
