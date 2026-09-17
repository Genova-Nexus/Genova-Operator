# Command Execution Guide — Genova Operator

`CommandExecutionEngine` provides a robust, boundary-enforced subprocess execution system for **Genova Operator**, enabling safe execution of shell scripts, CLI commands, and Python tools across projects like `GeneFusionAI` and `Clarify`.

---

## Overview

In the Genova ecosystem, decision plans are translated into concrete execution steps by `CommandExecutionEngine`:

1. **Subprocess Management**: Runs commands using standard `subprocess` routines with explicit non-blocking timeout controls.
2. **Workspace Boundary Protection**: Verifies working directory paths via `WorkspaceManager` to ensure commands do not escape configured project roots.
3. **Environment Isolation**: Injects custom environment variables per command request while protecting host credentials.
4. **Activity & Event Tracking**: Logs execution outcomes in `ProjectActivityTracker` and broadcasts events (`execution.started`, `execution.completed`, `execution.failed`, `execution.timed_out`) over `EventBus`.

---

## Data Models

### `CommandRequest`

```python
from genova_operator.execution import CommandRequest

request = CommandRequest(
    command=["python", "main.py", "--mode", "train"],
    cwd="/path/to/GeneFusionAI",
    env={"CUDA_VISIBLE_DEVICES": "0"},
    timeout_seconds=300.0,
    project_name="GeneFusionAI",
)
```

### `CommandResult`

```python
from genova_operator.execution import CommandResult, ExecutionStatus

result = engine.run_command(request)
if result.status == ExecutionStatus.SUCCESS:
    print(f"Executed in {result.duration_seconds:.2f}s:")
    print(result.stdout)
elif result.status == ExecutionStatus.TIMED_OUT:
    print("Execution timed out!")
else:
    print("Error:", result.error_message)
    print(result.stderr)
```

---

## Usage Examples

### 1. Initializing the Command Execution Engine

```python
from genova_operator import GenovaOperator
from genova_operator.execution import CommandExecutionEngine

operator = GenovaOperator()
operator.initialize()

engine = CommandExecutionEngine(
    workspace_manager=operator.get_component("workspace-manager"),
    activity_tracker=operator.get_component("project-activity"),
    operator=operator,
)
engine.initialize()
```

### 2. Running a Simple Command

```python
result = engine.run_simple_command(
    command=["pytest", "tests/"],
    cwd="/path/to/project",
    timeout_seconds=60.0,
    project_name="GeneFusionAI",
)
print("Exit code:", result.exit_code)
```
