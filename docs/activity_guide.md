# Project Activity Guide — Genova Operator (`Project Activity`)

The `Project Activity` component records recent executions, failures, file changes, running processes, and completed tasks to generate structured activity feeds and summaries consumed by **Genova Nexus**.

---

## 🎯 Activity Categories

- `EXECUTION`: Command, script, or task execution event.
- `FAILURE`: Process, task, or operation failure.
- `CHANGE`: File or configuration modification.
- `PROCESS_STARTED`: Process or task initiation.
- `PROCESS_STOPPED`: Process or task completion/cancellation.
- `TASK_COMPLETED`: Task successfully finished.
- `HEALTH_CHANGE`: Project health status change.
- `STATE_CHANGE`: Project state transition (`AVAILABLE`, `RUNNING`, etc.).

---

## 🎯 Key Capabilities

- **Automatic Event-Bus Auditing**: Subscribes to `EventBus` to automatically log task submissions, completions, failures, and state updates.
- **Activity Feeds & Summaries**: Provides project-level activity summaries (`ProjectActivitySummary`) and global activity feeds for Genova Nexus.
- **Filtering & Retrieval**: Filter by project name, category, or limit count.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ProjectActivityTracker, ActivityCategory

operator = GenovaOperator()
tracker = ProjectActivityTracker(operator=operator)

operator.register_component(tracker)
operator.initialize()

# Manually record an activity
tracker.record_activity(
    project_name="GeneFusionAI",
    category=ActivityCategory.EXECUTION,
    action="train_model",
    summary="Started DNA model training",
    task_id="task-101"
)

# Fetch project activity summary for Genova Nexus
summary = tracker.get_activity_summary("GeneFusionAI")
print(f"Project: {summary.project_name}")
print(f"Total Activities: {summary.total_activities_count}")
print(f"Failures: {summary.failures_count}")
```
