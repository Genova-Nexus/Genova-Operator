# Project Health Guide — Genova Operator (`Project Health`)

The `Project Health` component provides comprehensive 5-pillar operational health assessments for registered or target project directories (`GeneFusionAI`, `Clarify`, etc.).

---

## 🎯 Key Capabilities

- **5-Pillar Assessment**:
  1. **Existence & Accessibility**: Root folder permissions and availability.
  2. **Configuration Validity**: Config files (`genova_project.json`, `pyproject.toml`).
  3. **Runtime Environment Availability**: Python interpreter paths and virtual environments.
  4. **Dependencies Accessibility**: Requirements files (`requirements.txt`, `pyproject.toml`).
  5. **Structural Component Presence**: Source layouts (`src/`), entry scripts (`main.py`, `app.py`, `train.py`), and test suites (`tests/`).
- **Health Scoring**: Dynamic health score percentage (0–100%) and classification (`HEALTHY`, `DEGRADED`, `UNHEALTHY`, `UNAVAILABLE`).
- **Actionable Feedback**: Generates detailed issues and recommendations lists for Genova Nexus.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ProjectRegistry, ProjectHealthManager

operator = GenovaOperator()
registry = ProjectRegistry()
health_mgr = ProjectHealthManager(project_registry=registry)

registry.register_project("GeneFusionAI", "projects/GeneFusionAI")

operator.register_component(registry)
operator.register_component(health_mgr)
operator.initialize()

# Assess project health
report = health_mgr.assess_project_health("GeneFusionAI")

print(f"Project Health Status: {report.status.value}")
print(f"Health Score: {report.health_score}%")
print(f"Recommendations: {report.recommendations}")
```
