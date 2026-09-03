"""Unit tests for Genova Operator core architecture."""

import pytest

import genova_operator
from genova_operator.core.exceptions import (
    ComponentInitializationError,
    ComponentNotFoundError,
    TaskExecutionError,
)
from genova_operator.core.interfaces import BaseComponent, BaseTaskRunner
from genova_operator.core.operator import GenovaOperator
from genova_operator.core.types import (
    OperatorEvent,
    OperatorStatus,
    TaskRequest,
    TaskResult,
    TaskState,
)


class MockComponent(BaseComponent):
    """Mock sub-component for testing."""

    def __init__(self, name: str = "mock-component") -> None:
        self._name = name
        self._status = OperatorStatus.UNINITIALIZED
        self.initialized = False
        self.shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        self.initialized = True
        self._status = OperatorStatus.READY

    def shutdown(self) -> None:
        self.shutdown_called = True
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status


class FailingComponent(BaseComponent):
    """Failing sub-component for exception testing."""

    @property
    def name(self) -> str:
        return "failing-component"

    def initialize(self) -> None:
        raise RuntimeError("Initialization failed deliberately.")

    def shutdown(self) -> None:
        pass

    def get_status(self) -> OperatorStatus:
        return OperatorStatus.ERROR


class MockRunner(BaseComponent, BaseTaskRunner):
    """Mock runner component."""

    @property
    def name(self) -> str:
        return "mock-runner"

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_status(self) -> OperatorStatus:
        return OperatorStatus.READY

    def execute_task(self, request: TaskRequest) -> TaskResult:
        return TaskResult(
            task_id=request.task_id,
            status=TaskState.COMPLETED,
            action=request.action,
            project_name=request.project_name,
            exit_code=0,
            stdout="Executed via MockRunner",
        )

    def cancel_task(self, task_id: str) -> bool:
        return True


def test_operator_instantiation_and_initialization() -> None:
    """Test standard instantiation, initialization, and status transition."""
    operator = GenovaOperator(name="test-operator")
    assert operator.status == OperatorStatus.UNINITIALIZED

    comp = MockComponent()
    operator.register_component(comp)
    assert operator.has_component("mock-component")

    operator.initialize()
    assert operator.status == OperatorStatus.READY
    assert comp.initialized is True

    report = operator.get_status_report()
    assert report["name"] == "test-operator"
    assert report["status"] == "READY"
    assert report["components"]["mock-component"] == "READY"

    operator.shutdown()
    assert operator.status == OperatorStatus.SHUTDOWN
    assert comp.shutdown_called is True


def test_operator_initialization_failure() -> None:
    """Test that a failing sub-component raises ComponentInitializationError."""
    operator = GenovaOperator()
    operator.register_component(FailingComponent())

    with pytest.raises(ComponentInitializationError):
        operator.initialize()

    assert operator.status == OperatorStatus.ERROR


def test_get_component_not_found() -> None:
    """Test ComponentNotFoundError when accessing an unregistered component."""
    operator = GenovaOperator()
    with pytest.raises(ComponentNotFoundError):
        operator.get_component("nonexistent")


def test_event_bus_pub_sub() -> None:
    """Test thread-safe EventBus publish and subscribe functionality."""
    bus = genova_operator.EventBus()
    received_events = []

    def handler(event: OperatorEvent) -> None:
        received_events.append(event)

    bus.subscribe("task.completed", handler)

    event1 = OperatorEvent(event_type="task.completed", payload={"id": "1"})
    event2 = OperatorEvent(event_type="task.started", payload={"id": "2"})

    bus.publish(event1)
    bus.publish(event2)

    assert len(received_events) == 1
    assert received_events[0].payload["id"] == "1"

    # Test global subscriber
    global_events = []
    bus.subscribe("*", lambda e: global_events.append(e))
    bus.publish(event2)
    assert len(global_events) == 1

    bus.unsubscribe("task.completed", handler)
    assert bus.subscriber_count("task.completed") == 0


def test_task_request_and_result_serialization() -> None:
    """Test TaskRequest and TaskResult creation and dict serialization."""
    req = TaskRequest(
        action="inspect",
        project_name="GeneFusionAI",
        parameters={"depth": 2},
    )
    assert req.action == "inspect"
    assert req.project_name == "GeneFusionAI"

    data = req.to_dict()
    reconstructed_req = TaskRequest.from_dict(data)
    assert reconstructed_req.task_id == req.task_id
    assert reconstructed_req.action == req.action
    assert reconstructed_req.parameters == {"depth": 2}

    res = TaskResult(
        task_id=req.task_id,
        status=TaskState.COMPLETED,
        action=req.action,
        project_name=req.project_name,
        exit_code=0,
        stdout="OK",
    )
    assert res.is_success is True

    res_dict = res.to_dict()
    reconstructed_res = TaskResult.from_dict(res_dict)
    assert reconstructed_res.status == TaskState.COMPLETED
    assert reconstructed_res.stdout == "OK"


def test_task_submission_uninitialized() -> None:
    """Test submitting a task when operator is UNINITIALIZED raises TaskExecutionError."""
    operator = GenovaOperator()
    req = TaskRequest(action="test")
    with pytest.raises(TaskExecutionError):
        operator.submit_task(req)


def test_task_submission_with_custom_runner() -> None:
    """Test submit_task routes execution through a registered BaseTaskRunner."""
    operator = GenovaOperator()
    runner = MockRunner()
    operator.register_component(runner)
    operator.initialize()

    req = TaskRequest(action="run_experiment", project_name="Clarify")
    res = operator.submit_task(req)

    assert res.status == TaskState.COMPLETED
    assert res.stdout == "Executed via MockRunner"
