# Project State Guide — Genova Operator (`Project State`)

The `Project State` component manages lifecycle and operational states for projects (`GeneFusionAI`, `Clarify`, etc.), linking running tasks, health updates, and state change events.

---

## 🎯 Project State Model

- **`AVAILABLE`**: Project is registered, configured, and ready for operations.
- **`ACTIVE`**: Project is currently being accessed or was recently operational.
- **`INACTIVE`**: Project is idle with no recent activity.
- **`RUNNING`**: Project is actively executing commands or background tasks.
- **`UNHEALTHY`**: Project health checks are degraded or failing.
- **`UNAVAILABLE`**: Project filesystem directory is missing or inaccessible.

---

## 🎯 Key Capabilities

- **Active Task Coupling**: Automatically transitions project state to `RUNNING` when tasks begin, and reverts to `ACTIVE`/`AVAILABLE` when tasks finish.
- **Health Synchronization**: Syncs state with `ProjectHealthReport` diagnostics (`UNAVAILABLE`, `UNHEALTHY`, `AVAILABLE`).
- **Audit Trail & History**: Maintains `StateTransitionRecord` history per project.
- **EventBus Integration**: Emits `state.changed` events on every state transition.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ProjectRegistry, ProjectStateManager, ProjectState

operator = GenovaOperator()
registry = ProjectRegistry()
state_mgr = ProjectStateManager(project_registry=registry, operator=operator)

registry.register_project("GeneFusionAI", "projects/GeneFusionAI")

operator.register_component(registry)
operator.register_component(state_mgr)
operator.initialize()

# Query current state
state = state_mgr.get_project_state("GeneFusionAI")
print(f"GeneFusionAI State: {state.value}")

# Associate active task (transitions state to RUNNING)
state_mgr.associate_task("GeneFusionAI", "task-101")
print(f"State after task start: {state_mgr.get_project_state('GeneFusionAI').value}")

# Disassociate active task (reverts state to ACTIVE)
state_mgr.disassociate_task("GeneFusionAI", "task-101")
print(f"State after task end: {state_mgr.get_project_state('GeneFusionAI').value}")
```
