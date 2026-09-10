# Project Inspector Guide — Genova Operator (`Project Inspector`)

The `Project Inspector` component provides structured, comprehensive inspection of registered or target project directories (`GeneFusionAI`, `Clarify`, etc.).

---

## 🎯 Key Capabilities

- **Directory Hierarchy Analysis**: Generates structured `DirectoryTree` and `DirectoryNode` models representing files, folders, sizes, and file types.
- **Dependency & Framework Parsing**: Extracts dependencies from `requirements.txt`, `pyproject.toml`, and detects key frameworks (`torch`, `pandas`, `pytest`, `fastapi`).
- **Repository Inspection**: Inspects Git repository status, active branch, commit revision, and dirty status.
- **Environment & Entry Points Detection**: Identifies Python version, interpreter, set env vars, and entry scripts (`main.py`, `app.py`, `train.py`).
- **Structured Inspection Report**: Returns unified `ProjectInspectionReport` objects for Genova Nexus.

---

## 💻 Code Example

```python
from genova_operator import GenovaOperator, ProjectRegistry, ProjectInspector

operator = GenovaOperator()
registry = ProjectRegistry()
inspector = ProjectInspector(project_registry=registry)

registry.register_project("GeneFusionAI", "projects/GeneFusionAI")

operator.register_component(registry)
operator.register_component(inspector)
operator.initialize()

# Run project inspection
report = inspector.inspect_project("GeneFusionAI")

print(f"Project Name: {report.project_name}")
print(f"Total Files: {report.directory_tree.total_files}")
print(f"Frameworks Detected: {report.dependencies.frameworks}")
print(f"Entry Scripts: {report.entry_points.entry_scripts}")
```
