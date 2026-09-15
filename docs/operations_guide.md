# Project Operations Guide — Genova Operator

`ProjectOperationsManager` serves as the primary unified operational facade for **Genova Operator**. It aggregates project records, inspection reports, 5-pillar health checks, state summaries, activity feeds, and metadata into a single consolidated view and action interface.

---

## Overview

In the Genova Nexus / Operator architecture ("*Genova Nexus thinks, Genova Operator acts*"), **Genova Nexus** requires a single point of interaction to inspect, query, activate, and execute operations on registered projects. `ProjectOperationsManager`:

1. **Aggregates Operational Views**: Combines all Phase 2 project subsystems (`ProjectRegistry`, `ProjectInspector`, `ProjectHealthManager`, `ProjectStateManager`, `ProjectActivityTracker`, `ProjectMetadataManager`) into a single `ProjectOperationalView`.
2. **Standardizes Operational Dispatch**: Provides `execute_operation()` for system actions (`inspect`, `health_check`, `activate`, `deactivate`) and project-specific actions (e.g. `train`, `evaluate`).
3. **Records Executions**: Automatically logs activities and timing in `ProjectActivityTracker`.
4. **Broadcasts Events**: Emits `operation.started`, `operation.completed`, and `operation.failed` over `EventBus`.

---

## Data Models

### `ProjectOperationalView`

```python
from genova_operator.operations import ProjectOperationalView

view = ops_manager.get_operational_view("GeneFusionAI")
print("Health:", view.health_report["overall_status"])
print("State:", view.state_summary["current_state"])
print("Metadata Purpose:", view.metadata["purpose"])
```

### `OperationResult`

```python
from genova_operator.operations import OperationResult

result = ops_manager.execute_operation("GeneFusionAI", "activate")
if result.success:
    print(f"Operation {result.operation_name} succeeded in {result.execution_time_seconds:.2f}s")
```

---

## Usage Examples

### 1. Initializing the Operations Facade

```python
from genova_operator import GenovaOperator
from genova_operator.operations import ProjectOperationsManager

operator = GenovaOperator()
operator.initialize()

ops_manager = ProjectOperationsManager(
    project_registry=operator.get_component("project-registry"),
    project_inspector=operator.get_component("project-inspector"),
    health_manager=operator.get_component("project-health"),
    state_manager=operator.get_component("project-state"),
    activity_tracker=operator.get_component("project-activity"),
    metadata_manager=operator.get_component("project-metadata"),
    operator=operator,
)
ops_manager.initialize()
```

### 2. Querying Operational Views & Available Actions

```python
# Get consolidated snapshot
snapshot = ops_manager.get_operational_view("GeneFusionAI")
print(snapshot.to_dict())

# List all available actions
actions = ops_manager.list_available_operations("GeneFusionAI")
print("Available operations:", actions)
```

### 3. Executing Operations

```python
# Execute built-in health check
res_health = ops_manager.execute_operation("GeneFusionAI", "health_check")

# Execute state transition
res_activate = ops_manager.execute_operation("GeneFusionAI", "activate")

# Execute custom entry-point action
res_train = ops_manager.execute_operation("GeneFusionAI", "train", params={"epochs": 10})
```
