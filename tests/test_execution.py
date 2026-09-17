"""Unit tests for Command Execution Engine component in Genova Operator."""

import sys
from pathlib import Path
import pytest

from genova_operator.activity.manager import ProjectActivityTracker
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import OperatorStatus
from genova_operator.execution.engine import CommandExecutionEngine
from genova_operator.execution.models import (
    CommandRequest,
    CommandResult,
    ExecutionStatus,
)
from genova_operator.workspace.manager import WorkspaceManager


class TestExecutionModels:
    """Test suite for execution data models."""

    def test_command_request_serialization(self) -> None:
        req = CommandRequest(
            command=["python", "--version"],
            cwd="/tmp",
            env={"MY_VAR": "test"},
            timeout_seconds=30.0,
            project_name="TestProj",
        )
        data = req.to_dict()
        assert data["command"] == ["python", "--version"]
        assert data["timeout_seconds"] == 30.0

        deserialized = CommandRequest.from_dict(data)
        assert deserialized.command == ["python", "--version"]
        assert deserialized.env == {"MY_VAR": "test"}

    def test_command_result_serialization(self) -> None:
        res = CommandResult(
            command="echo hello",
            exit_code=0,
            stdout="hello\n",
            stderr="",
            duration_seconds=0.05,
            status=ExecutionStatus.SUCCESS,
        )
        data = res.to_dict()
        assert data["exit_code"] == 0
        assert data["status"] == "SUCCESS"

        deserialized = CommandResult.from_dict(data)
        assert deserialized.status == ExecutionStatus.SUCCESS
        assert deserialized.stdout == "hello\n"


class TestCommandExecutionEngine:
    """Test suite for CommandExecutionEngine."""

    def test_lifecycle(self) -> None:
        engine = CommandExecutionEngine()
        assert engine.get_status() == OperatorStatus.UNINITIALIZED
        engine.initialize()
        assert engine.get_status() == OperatorStatus.READY
        engine.shutdown()
        assert engine.get_status() == OperatorStatus.SHUTDOWN

    def test_successful_python_execution(self, tmp_path: Path) -> None:
        engine = CommandExecutionEngine()
        engine.initialize()

        cmd = [sys.executable, "-c", "print('Genova Engine Active')"]
        res = engine.run_simple_command(cmd, cwd=tmp_path)

        assert res.status == ExecutionStatus.SUCCESS
        assert res.exit_code == 0
        assert "Genova Engine Active" in res.stdout
        assert res.duration_seconds > 0.0

    def test_failing_command_execution(self, tmp_path: Path) -> None:
        engine = CommandExecutionEngine()
        engine.initialize()

        cmd = [sys.executable, "-c", "import sys; sys.exit(42)"]
        res = engine.run_simple_command(cmd, cwd=tmp_path)

        assert res.status == ExecutionStatus.FAILED
        assert res.exit_code == 42
        assert res.error_message is not None

    def test_command_timeout_handling(self, tmp_path: Path) -> None:
        engine = CommandExecutionEngine()
        engine.initialize()

        cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
        req = CommandRequest(command=cmd, cwd=str(tmp_path), timeout_seconds=0.2)
        res = engine.run_command(req)

        assert res.status == ExecutionStatus.TIMED_OUT
        assert res.exit_code == -1
        assert "timed out" in res.error_message.lower()

    def test_workspace_boundary_enforcement(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()

        ws_mgr = WorkspaceManager(root_path=ws_root)
        ws_mgr.initialize()

        engine = CommandExecutionEngine(workspace_manager=ws_mgr)
        engine.initialize()

        # Outside boundary directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        cmd = [sys.executable, "-c", "print('outside')"]
        req = CommandRequest(command=cmd, cwd=str(outside_dir))
        res = engine.run_command(req)

        assert res.status == ExecutionStatus.FAILED
        assert "boundary" in res.error_message.lower()

    def test_event_bus_and_activity_tracking(self, tmp_path: Path) -> None:
        op = GenovaOperator()
        op.initialize()

        act_tracker = ProjectActivityTracker(operator=op)
        act_tracker.initialize()

        engine = CommandExecutionEngine(activity_tracker=act_tracker, operator=op)
        engine.initialize()

        events = []
        op.event_bus.subscribe("execution.started", lambda e: events.append(e))
        op.event_bus.subscribe("execution.completed", lambda e: events.append(e))

        cmd = [sys.executable, "-c", "print('event_test')"]
        req = CommandRequest(command=cmd, cwd=str(tmp_path), project_name="EventProj")
        res = engine.run_command(req)

        assert res.status == ExecutionStatus.SUCCESS
        assert len(events) == 2
        assert events[0].event_type == "execution.started"
        assert events[1].event_type == "execution.completed"

        act_summary = act_tracker.get_activity_summary("EventProj")
        assert act_summary.total_activities_count >= 1

        op.shutdown()
