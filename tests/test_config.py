"""Unit tests for Genova Operator Configuration Manager."""

import json
import os
import pytest
from pathlib import Path

from genova_operator.config.manager import ConfigManager
from genova_operator.config.models import (
    AutomationConfig,
    ExecutionConfig,
    MonitoringConfig,
    OperatorConfig,
    ProjectConfig,
    WorkspaceConfig,
)
from genova_operator.config.validator import validate_config
from genova_operator.core.exceptions import ConfigurationError
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus


def test_default_config_instantiation() -> None:
    """Test default values of OperatorConfig."""
    config = OperatorConfig()
    assert config.workspace.root_path == "."
    assert config.workspace.projects_dir == "projects"
    assert config.execution.default_timeout == 300.0
    assert config.execution.max_concurrent_tasks == 5
    assert config.monitoring.polling_interval == 5.0
    assert config.automation.enable_scheduler is True
    assert len(config.projects) == 0


def test_project_config_isolation() -> None:
    """Test independent configuration for GeneFusionAI and Clarify."""
    genefusion_cfg = ProjectConfig(
        name="GeneFusionAI",
        path="projects/GeneFusionAI",
        environment_type="conda",
        python_interpreter="/envs/genefusion/bin/python",
        env_vars={"CUDA_VISIBLE_DEVICES": "0"},
        options={"batch_size": 32},
    )

    clarify_cfg = ProjectConfig(
        name="Clarify",
        path="projects/Clarify",
        environment_type="venv",
        python_interpreter="/envs/clarify/bin/python",
        env_vars={"LOG_LEVEL": "DEBUG"},
        options={"output_format": "json"},
    )

    op_config = OperatorConfig()
    op_config.set_project(genefusion_cfg)
    op_config.set_project(clarify_cfg)

    assert len(op_config.projects) == 2
    gf = op_config.get_project("GeneFusionAI")
    assert gf is not None
    assert gf.environment_type == "conda"
    assert gf.env_vars["CUDA_VISIBLE_DEVICES"] == "0"

    cl = op_config.get_project("Clarify")
    assert cl is not None
    assert cl.environment_type == "venv"
    assert cl.env_vars["LOG_LEVEL"] == "DEBUG"


def test_config_dict_serialization_and_deserialization() -> None:
    """Test converting OperatorConfig to and from dictionary."""
    config = OperatorConfig(
        workspace=WorkspaceConfig(root_path="/genova/workspace"),
        execution=ExecutionConfig(default_timeout=600.0),
    )
    p = ProjectConfig(name="GeneFusionAI", path="/genova/projects/GeneFusionAI")
    config.set_project(p)

    data = config.to_dict()
    assert data["workspace"]["root_path"] == "/genova/workspace"
    assert data["execution"]["default_timeout"] == 600.0
    assert "GeneFusionAI" in data["projects"]

    restored = OperatorConfig.from_dict(data)
    assert restored.workspace.root_path == "/genova/workspace"
    assert restored.execution.default_timeout == 600.0
    assert restored.get_project("GeneFusionAI") is not None


def test_config_file_loading_and_saving(tmp_path: Path) -> None:
    """Test saving and loading configuration JSON file via ConfigManager."""
    file_path = tmp_path / "operator_config.json"
    manager = ConfigManager()
    manager.config.workspace.root_path = str(tmp_path)
    manager.config.set_project(ProjectConfig(name="Clarify", path=str(tmp_path / "Clarify")))
    manager.save_to_file(file_path)

    assert file_path.is_file()

    new_manager = ConfigManager()
    new_manager.load_from_file(file_path)
    assert new_manager.config.workspace.root_path == str(tmp_path)
    assert new_manager.get_project_config("Clarify") is not None


def test_environment_variable_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test overriding configuration settings via environment variables."""
    monkeypatch.setenv("GENOVA_OPERATOR_WORKSPACE_ROOT_PATH", "/custom/workspace")
    monkeypatch.setenv("GENOVA_OPERATOR_EXECUTION_DEFAULT_TIMEOUT", "120.0")
    monkeypatch.setenv("GENOVA_OPERATOR_MONITORING_POLLING_INTERVAL", "2.5")

    manager = ConfigManager()
    manager.initialize()

    assert manager.config.workspace.root_path == "/custom/workspace"
    assert manager.config.execution.default_timeout == 120.0
    assert manager.config.monitoring.polling_interval == 2.5


def test_validation_errors() -> None:
    """Test that invalid values trigger ConfigurationError."""
    config = OperatorConfig()
    config.execution.default_timeout = -10.0
    with pytest.raises(ConfigurationError):
        validate_config(config)

    config2 = OperatorConfig()
    config2.monitoring.polling_interval = 0.0
    with pytest.raises(ConfigurationError):
        validate_config(config2)


def test_config_manager_component_integration() -> None:
    """Test registering ConfigManager with GenovaOperator core."""
    operator = GenovaOperator()
    config_mgr = ConfigManager()
    config_mgr.config.set_project(ProjectConfig(name="GeneFusionAI"))

    operator.register_component(config_mgr)
    operator.initialize()

    assert operator.has_component("operator-config")
    retrieved_mgr = operator.get_component("operator-config")
    assert isinstance(retrieved_mgr, ConfigManager)
    assert retrieved_mgr.get_status() == OperatorStatus.READY
    assert retrieved_mgr.get_project_config("GeneFusionAI") is not None
