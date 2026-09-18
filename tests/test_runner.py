"""Unit tests for SubprocessRunner component in Genova Operator."""

import sys
import time
from pathlib import Path
import pytest

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.runner.manager import SubprocessRunner
from genova_operator.runner.models import ProcessStatus, SubprocessHandle
from genova_operator.state.manager import ProjectStateManager
from genova_operator.state.models import ProjectState


class TestSubprocessModels:
    """Test suite for subprocess data models."""

    def test_subprocess_handle_serialization(self) -> None:
        handle = SubprocessHandle(
            process_id="proc_123",
            pid=1234,
            command=["python", "script.py"],
            cwd="/path/to/project",
            status=ProcessStatus.RUNNING,
            project_name="GeneFusionAI",
        )
        assert handle.is_alive is True

        data = handle.to_dict()
        assert data["process_id"] == "proc_123"
        assert data["pid"] == 1234
        assert data["status"] == "RUNNING"

        deserialized = SubprocessHandle.from_dict(data)
        assert deserialized.process_id == "proc_123"
        assert deserialized.status == ProcessStatus.RUNNING


class TestSubprocessRunner:
    """Test suite for SubprocessRunner."""

    def test_lifecycle(self) -> None:
        runner = SubprocessRunner()
        assert runner.get_status() == OperatorStatus.UNINITIALIZED
        runner.initialize()
        assert runner.get_status() == OperatorStatus.READY
        runner.shutdown()
        assert runner.get_status() == OperatorStatus.SHUTDOWN

    def test_start_and_complete_process(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "MyProject"
        proj_dir.mkdir()

        runner = SubprocessRunner()
        runner.initialize()

        cmd = [sys.executable, "-c", "import time; time.sleep(0.2); print('Task Output Line')"]
        handle = runner.start_process(cmd, cwd=proj_dir, project_name="MyProject")

        assert handle.process_id is not None
        assert handle.pid is not None
        assert handle.is_alive is True

        # Wait for completion
        time.sleep(0.6)
        updated = runner.get_process(handle.process_id)
        assert updated is not None
        assert updated.status == ProcessStatus.COMPLETED
        assert updated.exit_code == 0

        # Check tail logs
        logs = runner.tail_logs(handle.process_id)
        assert "Task Output Line" in logs

        runner.shutdown()

    def test_stop_process_gracefully(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "StopProject"
        proj_dir.mkdir()

        runner = SubprocessRunner()
        runner.initialize()

        cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
        handle = runner.start_process(cmd, cwd=proj_dir, project_name="StopProject")
        assert handle.is_alive is True

        stopped = runner.stop_process(handle.process_id, timeout_seconds=1.0)
        assert stopped.is_alive is False
        assert stopped.status in (ProcessStatus.STOPPED, ProcessStatus.KILLED)

        runner.shutdown()

    def test_state_and_activity_coupling(self, tmp_path: Path) -> None:
        proj_dir = tmp_path / "CoupledProj"
        proj_dir.mkdir()

        registry = ProjectRegistry(registry_file=tmp_path / "registry.json")
        registry.initialize()
        registry.register_project("CoupledProj", proj_dir)

        state_mgr = ProjectStateManager(project_registry=registry)
        state_mgr.initialize()

        act_tracker = ProjectActivityTracker()
        act_tracker.initialize()

        runner = SubprocessRunner(
            state_manager=state_mgr,
            activity_tracker=act_tracker,
        )
        runner.initialize()

        cmd = [sys.executable, "-c", "import time; time.sleep(0.3)"]
        handle = runner.start_process(cmd, cwd=proj_dir, project_name="CoupledProj")

        # Verify state transitioned to RUNNING
        assert state_mgr.get_project_state("CoupledProj") == ProjectState.RUNNING

        # Wait for process to complete
        time.sleep(0.6)
        runner.get_process(handle.process_id)

        # Verify state fallback to ACTIVE
        assert state_mgr.get_project_state("CoupledProj") == ProjectState.ACTIVE

        summary = act_tracker.get_activity_summary("CoupledProj")
        assert summary.total_activities_count >= 2

        runner.shutdown()
