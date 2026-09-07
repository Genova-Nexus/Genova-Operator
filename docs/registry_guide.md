# Project Registry Guide — Genova Operator (`Project Registry`)

The `Project Registry` acts as the central source of truth for all projects managed by **Genova Operator** (such as `GeneFusionAI` and `Clarify`).

---

## 🎯 Key Capabilities

- **Project Identity**: Standardized models for project name, display name, description, project type, and unique UUID.
- **Git & Environment Awareness**: Tracks Git remote URL, branch name, commit SHA hash, Python interpreter path, virtualenv type, environment variables, and dependencies.
- **Thread-Safe Registry**: Concurrent registration, lookup, listing, and filtering.
- **Persistence**: Save and restore registry records to/from JSON state files (`.genova/registry.json`).
- **Core Orchestrator Integration**: Implements `BaseComponent` and `BaseProjectRegistry` for `GenovaOperator`.

---

## 💻 Code Example

```python
from genova_operator import (
    GenovaOperator,
    ProjectRegistry,
    ProjectRecord,
    ProjectIdentity,
    RepositoryInfo,
    EnvironmentInfo,
)

operator = GenovaOperator()
registry = ProjectRegistry()

# Register GeneFusionAI
record_gf = ProjectRecord(
    identity=ProjectIdentity(
        name="GeneFusionAI",
        display_name="Gene Fusion AI",
        project_type="ml_research"
    ),
    path="projects/GeneFusionAI",
    repository=RepositoryInfo(
        remote_url="https://github.com/Genova-Nexus/GeneFusionAI.git",
        branch="main"
    ),
    environment=EnvironmentInfo(
        environment_type="conda",
        python_interpreter="/envs/genefusion/bin/python"
    ),
    entry_points={"train": "scripts/train.py"}
)

registry.register_project(name="GeneFusionAI", project_record=record_gf)

# Register Clarify
registry.register_project(name="Clarify", path="projects/Clarify")

operator.register_component(registry)
operator.initialize()

# Lookup registered project
proj = registry.get_project("GeneFusionAI")
print(f"Registered project path: {proj.path}")
```
