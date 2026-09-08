"""Genova Operator Project Discovery Package (`Project Discovery`).

Provides automatic project detection, confidence classification, and auto-registration
capabilities.
"""

from genova_operator.discovery.manager import ProjectDiscovery
from genova_operator.discovery.models import DiscoveredProject, ProjectConfidence
from genova_operator.discovery.rules import evaluate_directory

__all__ = [
    "ProjectDiscovery",
    "DiscoveredProject",
    "ProjectConfidence",
    "evaluate_directory",
]
