# Core Diagnostics Guide — Genova Operator (`Core Diagnostics`)

The `Core Diagnostics` component validates foundation health, component readiness, workspace boundaries, registry integrity, and discovery capabilities across the entire **Genova Operator** framework.

---

## 🎯 Key Capabilities

- **System Diagnostics**: Executes structured health checks across `Core Orchestrator`, `ConfigManager`, `WorkspaceManager`, `ProjectRegistry`, and `ProjectDiscovery`.
- **Target Project Benchmarking**: Validates workspace setup, discovery, registration, and task execution against `GeneFusionAI` and `Clarify` workloads.
- **Diagnostic Reports**: Generates a comprehensive `DiagnosticReport` summarizing check counts, durations, details, and overall health status (`HEALTHY`, `DEGRADED`, `UNHEALTHY`).

---

## 💻 Code Example

```python
from genova_operator import (
    GenovaOperator,
    ConfigManager,
    WorkspaceManager,
    ProjectRegistry,
    ProjectDiscovery,
    CoreDiagnostics,
)

operator = GenovaOperator()
config_mgr = ConfigManager()
ws_mgr = WorkspaceManager()
registry = ProjectRegistry()
discovery = ProjectDiscovery(workspace_manager=ws_mgr, project_registry=registry)
diagnostics = CoreDiagnostics(operator=operator)

# Register components
operator.register_component(config_mgr)
operator.register_component(ws_mgr)
operator.register_component(registry)
operator.register_component(discovery)
operator.register_component(diagnostics)

operator.initialize()

# Run foundation diagnostics
report = diagnostics.run_diagnostics()
print(f"Overall Status: {report.overall_status}")
print(f"Passed: {report.passed_count}/{report.total_checks}")

for check in report.checks:
    print(f"  [{check.status.value}] {check.name}: {check.message}")
```
