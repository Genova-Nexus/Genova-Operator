"""Project Metadata models for Genova Operator.

Defines standardized, configurable operational metadata schemas describing project purpose,
primary technologies, environment requirements, supported operations, and custom attributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectMetadata:
    """Standardized operational metadata model for a Genova project.

    Attributes:
        purpose: Domain or scientific purpose description.
        primary_technologies: List of technologies/frameworks used (e.g. ['Python', 'PyTorch']).
        supported_operations: List of operational actions supported (e.g. ['inspect', 'train', 'evaluate']).
        entry_points: Dict mapping operational action to script path.
        environment_requirements: Requirements dict (e.g. {'min_python': '3.9', 'gpu_required': True}).
        maintainers: List of maintainers or authors.
        tags: Classification tags (e.g. ['genomics', 'ml']).
        custom_attributes: Key-value map for project-specific custom attributes.
    """
    purpose: str = ""
    primary_technologies: List[str] = field(default_factory=list)
    supported_operations: List[str] = field(default_factory=list)
    entry_points: Dict[str, str] = field(default_factory=dict)
    environment_requirements: Dict[str, Any] = field(default_factory=dict)
    maintainers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)

    def supports_operation(self, operation: str) -> bool:
        """Return True if operation is listed in supported_operations or entry_points."""
        op_lower = operation.lower()
        ops_lower = [op.lower() for op in self.supported_operations]
        return op_lower in ops_lower or op_lower in self.entry_points

    def to_dict(self) -> Dict[str, Any]:
        return {
            "purpose": self.purpose,
            "primary_technologies": self.primary_technologies,
            "supported_operations": self.supported_operations,
            "entry_points": self.entry_points,
            "environment_requirements": self.environment_requirements,
            "maintainers": self.maintainers,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectMetadata:
        return cls(
            purpose=str(data.get("purpose", "")),
            primary_technologies=list(data.get("primary_technologies", [])),
            supported_operations=list(data.get("supported_operations", [])),
            entry_points=dict(data.get("entry_points", {})),
            environment_requirements=dict(data.get("environment_requirements", {})),
            maintainers=list(data.get("maintainers", [])),
            tags=list(data.get("tags", [])),
            custom_attributes=dict(data.get("custom_attributes", {})),
        )
