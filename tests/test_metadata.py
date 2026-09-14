"""Unit tests for Project Metadata component in Genova Operator."""

import json
from pathlib import Path
import pytest

from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.metadata.manager import ProjectMetadataManager
from genova_operator.metadata.models import ProjectMetadata
from genova_operator.registry.manager import ProjectRegistry


class TestProjectMetadataModel:
    """Test suite for ProjectMetadata data model."""

    def test_default_metadata(self) -> None:
        meta = ProjectMetadata()
        assert meta.purpose == ""
        assert meta.primary_technologies == []
        assert meta.supported_operations == []
        assert meta.entry_points == {}
        assert meta.environment_requirements == {}
        assert meta.maintainers == []
        assert meta.tags == []
        assert meta.custom_attributes == {}

    def test_supports_operation(self) -> None:
        meta = ProjectMetadata(
            supported_operations=["inspect", "train"],
            entry_points={"evaluate": "eval.py"},
        )
        assert meta.supports_operation("inspect") is True
        assert meta.supports_operation("INSPECT") is True
        assert meta.supports_operation("train") is True
        assert meta.supports_operation("evaluate") is True
        assert meta.supports_operation("deploy") is False

    def test_dict_serialization(self) -> None:
        meta = ProjectMetadata(
            purpose="Genomics analysis pipeline",
            primary_technologies=["Python", "PyTorch"],
            supported_operations=["train", "predict"],
            entry_points={"train": "train.py"},
            environment_requirements={"min_python": "3.10"},
            maintainers=["Dev Team"],
            tags=["genomics", "ml"],
            custom_attributes={"model_type": "transformer"},
        )
        data = meta.to_dict()
        assert data["purpose"] == "Genomics analysis pipeline"
        assert data["primary_technologies"] == ["Python", "PyTorch"]
        assert data["custom_attributes"]["model_type"] == "transformer"

        deserialized = ProjectMetadata.from_dict(data)
        assert deserialized.purpose == meta.purpose
        assert deserialized.primary_technologies == meta.primary_technologies
        assert deserialized.entry_points == meta.entry_points
        assert deserialized.custom_attributes == meta.custom_attributes


class TestProjectMetadataManager:
    """Test suite for ProjectMetadataManager."""

    def test_lifecycle(self) -> None:
        manager = ProjectMetadataManager()
        assert manager.get_status() == OperatorStatus.UNINITIALIZED
        manager.initialize()
        assert manager.get_status() == OperatorStatus.READY
        manager.shutdown()
        assert manager.get_status() == OperatorStatus.SHUTDOWN

    def test_get_and_set_metadata(self) -> None:
        manager = ProjectMetadataManager()
        manager.initialize()

        meta = ProjectMetadata(
            purpose="Test Purpose",
            supported_operations=["test", "build"],
        )
        manager.set_metadata("test_proj", meta)

        retrieved = manager.get_metadata("test_proj")
        assert retrieved.purpose == "Test Purpose"
        assert retrieved.supports_operation("test") is True
        assert manager.list_supported_operations("test_proj") == ["test", "build"]
        assert manager.supports_operation("test_proj", "build") is True

    def test_set_metadata_publishes_event(self) -> None:
        op = GenovaOperator()
        op.initialize()

        manager = ProjectMetadataManager(operator=op)
        manager.initialize()

        received_events = []
        op.event_bus.subscribe("metadata.updated", lambda e: received_events.append(e))

        meta = ProjectMetadata(purpose="Event test")
        manager.set_metadata("event_proj", meta)

        assert len(received_events) == 1
        assert received_events[0].payload["project_name"] == "event_proj"
        assert received_events[0].payload["metadata"]["purpose"] == "Event test"
        op.shutdown()

    def test_extract_metadata_from_json(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "my_project"
        proj_dir.mkdir()
        
        manifest = proj_dir / "genova_project.json"
        manifest.write_text(
            json.dumps({
                "purpose": "Bioinformatics variant caller",
                "technologies": ["Python", "Rust"],
                "operations": ["call_variants", "benchmark"],
                "entry_points": {"call": "cli.py"},
                "maintainers": ["Alice"],
                "tags": ["variant-calling"],
                "custom_attributes": {"version": "1.0.0"},
            }),
            encoding="utf-8",
        )

        manager = ProjectMetadataManager()
        extracted = manager.extract_metadata_from_project(proj_dir)

        assert extracted.purpose == "Bioinformatics variant caller"
        assert extracted.primary_technologies == ["Python", "Rust"]
        assert "call_variants" in extracted.supported_operations
        assert extracted.entry_points == {"call": "cli.py"}
        assert extracted.maintainers == ["Alice"]
        assert extracted.tags == ["variant-calling"]
        assert extracted.custom_attributes == {"version": "1.0.0"}

    def test_extract_metadata_auto_inference(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "infer_project"
        proj_dir.mkdir()

        (proj_dir / "main.py").write_text("# main entry point\n", encoding="utf-8")
        (proj_dir / "tests").mkdir()
        (proj_dir / "requirements.txt").write_text("torch>=2.0.0\npandas\nfastapi\n", encoding="utf-8")

        manager = ProjectMetadataManager()
        extracted = manager.extract_metadata_from_project(proj_dir)

        assert "Python" in extracted.primary_technologies
        assert "PyTorch" in extracted.primary_technologies
        assert "Pandas" in extracted.primary_technologies
        assert "FastAPI" in extracted.primary_technologies
        assert "execute" in extracted.supported_operations
        assert "test" in extracted.supported_operations

    def test_integration_with_registry(self, tmp_path: Path) -> None:
        registry_file = tmp_path / "registry.json"
        registry = ProjectRegistry(registry_file=registry_file)
        registry.initialize()

        proj1 = tmp_path / "proj1"
        proj1.mkdir()
        (proj1 / "genova_project.json").write_text(
            json.dumps({"purpose": "Registry Project 1", "operations": ["run"]}),
            encoding="utf-8",
        )
        registry.register_project("proj1", proj1)

        manager = ProjectMetadataManager(project_registry=registry)
        manager.initialize()

        meta1 = manager.get_metadata("proj1")
        assert meta1.purpose == "Registry Project 1"
        assert meta1.supported_operations == ["run"]

        # Update metadata via manager and verify registry record is updated
        new_meta = ProjectMetadata(purpose="Updated Purpose", supported_operations=["run", "test"])
        manager.set_metadata("proj1", new_meta)

        rec = registry.get_project("proj1")
        assert rec is not None
        assert rec.metadata["purpose"] == "Updated Purpose"
        assert rec.metadata["supported_operations"] == ["run", "test"]

        registry.shutdown()
