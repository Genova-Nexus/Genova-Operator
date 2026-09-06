# Workspace Guide — Genova Operator (`Workspace Manager`)

The `Workspace Manager` defines workspace boundaries, directory path resolution, health diagnostics, candidate project directory scanning, and marker file management.

---

## 🎯 Key Capabilities

- **Path Boundary Resolution**: Ensures operational file accesses remain safely within the workspace boundary.
- **Workspace Health Diagnostics**: Checks directory existence, write permissions, disk space, and structure health.
- **Candidate Project Discovery**: Scans the configured `projects` directory for candidate projects (`GeneFusionAI`, `Clarify`, etc.).
- **Workspace Markers**: Supports `.genova/workspace.json` marker files to define workspace identities.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ConfigManager, WorkspaceManager

operator = GenovaOperator()
config_mgr = ConfigManager()
ws_mgr = WorkspaceManager(config_manager=config_mgr)

operator.register_component(config_mgr)
operator.register_component(ws_mgr)
operator.initialize()

# Check workspace health
health = ws_mgr.check_health()
print(f"Workspace healthy: {health.is_healthy}")

# Scan candidate project directories
candidates = ws_mgr.find_candidate_project_dirs()
print(f"Found project candidates: {candidates}")
```
