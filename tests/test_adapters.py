"""Unit tests for Project Adapters component in Genova Operator."""

import json
from pathlib import Path
import pytest

from genova_operator.adapters.clarify import ClarifyAdapter
from genova_operator.adapters.genefusionai import GeneFusionAIAdapter
from genova_operator.adapters.manager import ProjectAdapterRegistry
from genova_operator.core.types import OperatorStatus


class TestGeneFusionAIAdapter:
    """Test suite for GeneFusionAIAdapter."""

    def test_adapter_properties(self) -> None:
        adapter = GeneFusionAIAdapter()
        assert adapter.name == "GeneFusionAIAdapter"
        assert adapter.adapter_type == "genomics_ml"
        assert "detect_fusions" in adapter.list_supported_actions()

    def test_is_applicable(self, tmp_path: Path) -> None:
        adapter = GeneFusionAIAdapter()
        gf_dir = tmp_path / "GeneFusionAI"
        gf_dir.mkdir()
        assert adapter.is_applicable(gf_dir) is True

        other_dir = tmp_path / "OtherApp"
        other_dir.mkdir()
        assert adapter.is_applicable(other_dir) is False

        (other_dir / "genova_project.json").write_text(
            json.dumps({"adapter": "GeneFusionAI"}), encoding="utf-8"
        )
        assert adapter.is_applicable(other_dir) is True

    def test_execute_action(self, tmp_path: Path) -> None:
        adapter = GeneFusionAIAdapter()
        gf_dir = tmp_path / "GeneFusionAI"
        gf_dir.mkdir()

        res_detect = adapter.execute_action("detect_fusions", gf_dir, {"sample_id": "HG002"})
        assert res_detect["status"] == "COMPLETED"
        assert len(res_detect["fusions_detected"]) >= 1

        res_train = adapter.execute_action("train_model", gf_dir, {"epochs": 3})
        assert res_train["status"] == "COMPLETED"
        assert res_train["epochs"] == 3


class TestClarifyAdapter:
    """Test suite for ClarifyAdapter."""

    def test_adapter_properties(self) -> None:
        adapter = ClarifyAdapter()
        assert adapter.name == "ClarifyAdapter"
        assert adapter.adapter_type == "clinical_nlp_imaging"
        assert "analyze_image" in adapter.list_supported_actions()

    def test_is_applicable(self, tmp_path: Path) -> None:
        adapter = ClarifyAdapter()
        clarify_dir = tmp_path / "Clarify"
        clarify_dir.mkdir()
        assert adapter.is_applicable(clarify_dir) is True

        other_dir = tmp_path / "OtherApp"
        other_dir.mkdir()
        assert adapter.is_applicable(other_dir) is False

    def test_execute_action(self, tmp_path: Path) -> None:
        adapter = ClarifyAdapter()
        clarify_dir = tmp_path / "Clarify"
        clarify_dir.mkdir()

        res_analyze = adapter.execute_action("analyze_image", clarify_dir)
        assert res_analyze["status"] == "COMPLETED"
        assert "findings" in res_analyze

        res_report = adapter.execute_action("generate_report", clarify_dir, {"patient_id": "P101"})
        assert res_report["status"] == "COMPLETED"
        assert res_report["patient_id"] == "P101"


class TestProjectAdapterRegistry:
    """Test suite for ProjectAdapterRegistry."""

    def test_registry_lifecycle_and_lookup(self, tmp_path: Path) -> None:
        registry = ProjectAdapterRegistry()
        assert registry.get_status() == OperatorStatus.UNINITIALIZED
        registry.initialize()
        assert registry.get_status() == OperatorStatus.READY

        adapters = registry.list_adapters()
        assert "GeneFusionAIAdapter" in adapters
        assert "ClarifyAdapter" in adapters

        gf_dir = tmp_path / "GeneFusionAI"
        gf_dir.mkdir()
        adapter = registry.find_adapter_for_project(gf_dir)
        assert adapter is not None
        assert adapter.name == "GeneFusionAIAdapter"

        clarify_dir = tmp_path / "Clarify"
        clarify_dir.mkdir()
        res = registry.execute_action(clarify_dir, "generate_report")
        assert res["status"] == "COMPLETED"

        registry.shutdown()
        assert registry.get_status() == OperatorStatus.SHUTDOWN
