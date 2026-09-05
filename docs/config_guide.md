# Configuration Guide — Genova Operator (`Operator Config`)

The `Operator Config` component manages workspace locations, registered projects, execution parameters, resource monitoring, and automation settings.

---

## 🎯 Key Capabilities

- **Layered Resolution**: Default Settings $\rightarrow$ Configuration Files $\rightarrow$ Programmatic Dicts $\rightarrow$ Environment Overrides.
- **Project Isolation**: Independent configuration per project (e.g. `GeneFusionAI`, `Clarify`).
- **Validation**: Enforces non-negative timeouts, positive polling intervals, and path checking.
- **Core Component Integration**: Integrates directly as a `BaseComponent` within `GenovaOperator`.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ConfigManager, ProjectConfig

# Create core operator and config manager
operator = GenovaOperator()
config_mgr = ConfigManager()

# Configure project settings for GeneFusionAI and Clarify
config_mgr.set_project_config(ProjectConfig(
    name="GeneFusionAI",
    path="projects/GeneFusionAI",
    environment_type="conda",
    python_interpreter="/envs/genefusion/bin/python",
    env_vars={"CUDA_VISIBLE_DEVICES": "0"}
))

config_mgr.set_project_config(ProjectConfig(
    name="Clarify",
    path="projects/Clarify",
    environment_type="venv"
))

# Register and initialize
operator.register_component(config_mgr)
operator.initialize()
```

---

## 🌐 Environment Overrides

Configuration parameters can be overridden using environment variables prefixed with `GENOVA_OPERATOR_`:

| Environment Variable | Target Setting | Default |
| :--- | :--- | :--- |
| `GENOVA_OPERATOR_WORKSPACE_ROOT_PATH` | `workspace.root_path` | `.` |
| `GENOVA_OPERATOR_WORKSPACE_PROJECTS_DIR` | `workspace.projects_dir` | `projects` |
| `GENOVA_OPERATOR_EXECUTION_DEFAULT_TIMEOUT` | `execution.default_timeout` | `300.0` |
| `GENOVA_OPERATOR_MONITORING_POLLING_INTERVAL` | `monitoring.polling_interval` | `5.0` |
| `GENOVA_OPERATOR_AUTOMATION_ENABLE_SCHEDULER` | `automation.enable_scheduler` | `true` |
