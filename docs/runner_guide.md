# Subprocess Runner Guide — Genova Operator

`SubprocessRunner` provides a thread-safe background process management subsystem for **Genova Operator**, enabling execution, PID tracking, log streaming, and graceful termination of asynchronous tools, servers, and long-running research tasks.

---

## Overview

While `CommandExecutionEngine` handles synchronous, short-lived shell command executions, long-running processes (e.g. model training scripts, web servers, background data pipelines) require asynchronous background management. `SubprocessRunner`:

1. **Spawns Background Processes**: Runs non-blocking processes using `subprocess.Popen`.
2. **Tracks PIDs & Status**: Maintains active process handles (`SubprocessHandle`) and polls OS status (`RUNNING`, `COMPLETED`, `FAILED`, `STOPPED`).
3. **Streams Output Logs**: Directs stdout and stderr to dedicated project log files (`.genova/logs/<process_id>.log`).
4. **Couples Project State**: Automatically transitions target project state to `RUNNING` via `ProjectStateManager.associate_task()`.
5. **Provides Graceful Termination**: Terminates processes safely via SIGTERM timeout with SIGKILL fallback (`stop_process()`).

---

## Data Models

### `SubprocessHandle`

```python
from genova_operator.runner import SubprocessHandle

handle = runner.get_process(process_id="proc_123456")
if handle and handle.is_alive:
    print(f"Process {handle.pid} is running.")
```

---

## Usage Examples

### 1. Initializing SubprocessRunner

```python
from genova_operator import GenovaOperator
from genova_operator.runner import SubprocessRunner

operator = GenovaOperator()
operator.initialize()

runner = SubprocessRunner(
    workspace_manager=operator.get_component("workspace-manager"),
    state_manager=operator.get_component("project-state"),
    activity_tracker=operator.get_component("project-activity"),
    operator=operator,
)
runner.initialize()
```

### 2. Spawning a Background Process

```python
handle = runner.start_process(
    command=["python", "train.py", "--epochs", "100"],
    cwd="/path/to/GeneFusionAI",
    project_name="GeneFusionAI",
)

print("Started process ID:", handle.process_id)
print("Log file:", handle.log_file)
```

### 3. Tailing Logs & Stopping Processes

```python
# Tail output logs
log_output = runner.tail_logs(handle.process_id, max_lines=50)
print(log_output)

# Stop process gracefully
stopped_handle = runner.stop_process(handle.process_id, timeout_seconds=5.0)
print("Final status:", stopped_handle.status)
```
