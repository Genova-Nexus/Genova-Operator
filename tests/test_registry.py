"""Unit tests for Genova Operator Project Registry."""

import pytest
from pathlib import Path

from genova_operator.core.exceptions import ProjectNotFoundError
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import (
    EnvironmentInfo,
    ProjectIdentity,
    ProjectRecord,
    RepositoryInfo,
)


def test_project_record_creation_and_dict_serialization() -> None:
    """Test ProjectRecord, ProjectIdentity, RepositoryInfo, and EnvironmentInfo serialization."""
    identity = ProjectIdentity(
        name="GeneFusionAI",
        display_name="Gene Fusion AI",
        description="Gene fusion machine learning pipeline",
        project_type="ml_research",
    )
    repo = RepositoryInfo(
        remote_url="https://github.com/Genova-Nexus/GeneFusionAI.git",
        branch="main",
        commit_hash="abc1234",
    )
    env = EnvironmentInfo(
        environment_type="conda",
        python_interpreter="/envs/genefusion/bin/python",
        env_vars={"CUDA_VISIBLE_DEVICES": "0"},
        dependencies=["torch", "numpy", "pandas"],
    )

    record = ProjectRecord(
        identity=identity,
        path="projects/GeneFusionAI",
        repository=repo,
        environment=env,
        entry_points={"train": "scripts/train.py", "eval": "scripts/eval.py"},
        available_commands=["pytest", "python scripts/train.py"],
    )

    assert record.name == "GeneFusionAI"
    data = record.to_dict()
    assert data["identity"]["name"] == "GeneFusionAI"
    assert data["repository"]["branch"] == "main"
    assert data["environment"]["environment_type"] == "conda"

    restored = ProjectRecord.from_dict(data)
    assert restored.name == "GeneFusionAI"
    assert restored.repository.commit_hash == "abc1234"
    assert restored.environment.env_vars["CUDA_VISIBLE_DEVICES"] == "0"
    assert restored.entry_points["train"] == "scripts/train.py"


def test_register_and_lookup_projects() -> None:
    """Test registering and looking up GeneFusionAI and Clarify projects."""
    registry = ProjectRegistry()
    registry.initialize()

    record_gf = registry.register_project(
        name="GeneFusionAI",
        path="projects/GeneFusionAI",
        config={"type": "ml"},
    )
    record_cl = registry.register_project(
        name="Clarify",
        path="projects/Clarify",
        config={"type": "research"},
    )

    assert registry.count() == 2
    assert registry.has_project("GeneFusionAI") is True
    assert registry.has_project("Clarify") is True

    gf = registry.get_project("GeneFusionAI")
    assert gf is not None
    assert gf.path == "projects/GeneFusionAI"

    cl = registry.get_project_or_raise("Clarify")
    assert cl.path == "projects/Clarify"

    with pytest.raises(ProjectNotFoundError):
        registry.get_project_or_raise("UnknownProject")


def test_unregister_project() -> None:
    """Test unregistering a project from registry."""
    registry = ProjectRegistry()
    registry.register_project("Clarify", "projects/Clarify")
    assert registry.has_project("Clarify") is True

    removed = registry.unregister_project("Clarify")
    assert removed is True
    assert registry.has_project("Clarify") is False
    assert registry.count() == 0


def test_registry_file_persistence(tmp_path: Path) -> None:
    """Test saving and loading ProjectRegistry state to/from JSON file."""
    reg_file = tmp_path / "registry.json"
    registry = ProjectRegistry(registry_file=reg_file)

    registry.register_project("GeneFusionAI", "projects/GeneFusionAI")
    registry.register_project("Clarify", "projects/Clarify")
    registry.save_to_file(reg_file)

    assert reg_file.is_file()

    new_registry = ProjectRegistry(registry_file=reg_file)
    new_registry.initialize()

    assert new_registry.count() == 2
    assert new_registry.has_project("GeneFusionAI") is True
    assert new_registry.has_project("Clarify") is True


def test_project_registry_component_integration() -> None:
    """Test integrating ProjectRegistry into GenovaOperator core."""
    operator = GenovaOperator()
    registry = ProjectRegistry()
    registry.register_project("GeneFusionAI", "projects/GeneFusionAI")

    operator.register_component(registry)
    operator.initialize()

    assert operator.has_component("project-registry")
    retrieved = operator.get_component("project-registry")
    assert isinstance(retrieved, ProjectRegistry)
    assert retrieved.get_status() == OperatorStatus.READY
    assert retrieved.has_project("GeneFusionAI") is True
