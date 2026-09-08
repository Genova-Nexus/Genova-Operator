# Project Discovery Guide — Genova Operator (`Project Discovery`)

The `Project Discovery` component automatically scans workspaces to detect software, ML research, and application projects (such as `GeneFusionAI` and `Clarify`).

---

## 🎯 Key Capabilities

- **Rule Engine**: Evaluates explicit project markers (`genova_project.json`, `.genova/project.json`), Python package definitions (`pyproject.toml`, `setup.py`, `requirements.txt`), Git repositories (`.git`), and code structural layouts (`src/`, `tests/`, `main.py`).
- **Confidence Scoring**: Classifies directories with confidence levels (`HIGH`, `MEDIUM`, `LOW`, `NOT_A_PROJECT`).
- **Auto-Registration**: Converts `DiscoveredProject` instances directly into `ProjectRecord` models and populates `ProjectRegistry`.
- **Filtering**: Filters out hidden folders (`.git`, `.venv`), build directories (`dist`, `build`), and ordinary plain directories.

---

## 💻 Code Example

```python
from genova_operator import (
    GenovaOperator,
    WorkspaceManager,
    ProjectRegistry,
    ProjectDiscovery,
    ProjectConfidence,
)

operator = GenovaOperator()
ws_mgr = WorkspaceManager(projects_dir="projects")
registry = ProjectRegistry()
discovery = ProjectDiscovery(workspace_manager=ws_mgr, project_registry=registry)

operator.register_component(ws_mgr)
operator.register_component(registry)
operator.register_component(discovery)
operator.initialize()

# Discover projects with confidence >= MEDIUM
found = discovery.discover_projects(min_confidence=ProjectConfidence.MEDIUM)
for p in found:
    print(f"Found project: {p.name} (confidence: {p.confidence.value})")

# Auto-register into ProjectRegistry
discovery.auto_register_discovered()
print(f"Total registered in registry: {registry.count()}")
```
