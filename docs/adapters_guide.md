# Project Adapters Guide — Genova Operator

`ProjectAdapterRegistry` and `BaseProjectAdapter` provide domain-specific integration layers for projects operating within the Genova ecosystem, such as `GeneFusionAI` (genomics ML) and `Clarify` (clinical imaging/NLP).

---

## Overview

While **Genova Operator** handles core software lifecycle operations (inspection, health assessment, state tracking, activity logging, and task execution), individual research and clinical projects often have unique domain requirements. Project Adapters bridge core operator capabilities with domain-specific actions.

1. **`GeneFusionAIAdapter`**: Manages genomics ML project requirements, PyTorch environment checks, and domain execution (`detect_fusions`, `train_model`, `evaluate_metrics`).
2. **`ClarifyAdapter`**: Manages clinical imaging/NLP requirements, FastAPI environment checks, and domain execution (`analyze_image`, `generate_report`, `run_server`).
3. **`ProjectAdapterRegistry`**: Dispatches operational queries and actions to the correct adapter based on project directory inspection or manifest settings.

---

## Data Models & Abstract Interface

```python
from genova_operator.adapters import BaseProjectAdapter, ProjectAdapterRegistry

class CustomDomainAdapter(BaseProjectAdapter):
    @property
    def name(self) -> str:
        return "CustomDomainAdapter"

    @property
    def adapter_type(self) -> str:
        return "bioinformatics"

    def is_applicable(self, project_path) -> bool:
        return (project_path / "bio_manifest.json").is_file()

    def inspect_adapter_status(self, project_path):
        return {"ready": True, "adapter_name": self.name}

    def list_supported_actions(self):
        return ["run_pipeline", "export_data"]

    def execute_action(self, action_name, project_path, params=None):
        return {"action": action_name, "status": "COMPLETED"}
```

---

## Usage Examples

### 1. Registering & Finding Adapters

```python
from genova_operator.adapters import ProjectAdapterRegistry

registry = ProjectAdapterRegistry()
registry.initialize()

# Auto-detect adapter for project path
adapter = registry.find_adapter_for_project("/path/to/GeneFusionAI")
if adapter:
    print(f"Found adapter: {adapter.name} ({adapter.adapter_type})")
```

### 2. Executing Domain Actions

```python
# Execute genomics fusion detection
result = registry.execute_action(
    project_path="/path/to/GeneFusionAI",
    action_name="detect_fusions",
    params={"sample_id": "HG002"},
)
print("Fusions detected:", result["fusions_detected"])

# Execute clinical report generation
result_clarify = registry.execute_action(
    project_path="/path/to/Clarify",
    action_name="generate_report",
    params={"patient_id": "P101"},
)
print("Clarification summary:", result_clarify["summary"])
```
