# Project Metadata Guide — Genova Operator

`ProjectMetadataManager` provides a standardized operational metadata model describing project purpose, primary technologies, environment requirements, entry points, supported operational actions, maintainers, classification tags, and custom attributes.

---

## Overview

In Genova Operator, operational decision-making relies on structured metadata extracted from projects. `ProjectMetadataManager`:

1. **Auto-Extracts Metadata**: Reads `genova_project.json` or `.genova/project.json` manifest files.
2. **Infers Operational Defaults**: Automatically infers supported operations (e.g. `execute`, `test`) and primary technologies (e.g. `Python`, `PyTorch`, `Pandas`, `FastAPI`) if manifests are absent.
3. **Supports Custom Metadata**: Maintains custom operational key-value attributes per project.
4. **Notifies EventBus**: Publishes `metadata.updated` events whenever project metadata changes.

---

## Data Models

### `ProjectMetadata`

```python
from genova_operator.metadata import ProjectMetadata

metadata = ProjectMetadata(
    purpose="Bioinformatics variant caller and ML pipeline",
    primary_technologies=["Python", "PyTorch", "Pandas"],
    supported_operations=["inspect", "train", "evaluate"],
    entry_points={"train": "scripts/train.py", "eval": "scripts/evaluate.py"},
    environment_requirements={"min_python": "3.10", "gpu_required": True},
    maintainers=["Genova Team"],
    tags=["genomics", "machine-learning"],
    custom_attributes={"dataset": "HG002"},
)
```

---

## Operations & Methods

### 1. Initialize & Shutdown

```python
from genova_operator.metadata import ProjectMetadataManager

manager = ProjectMetadataManager(project_registry=registry)
manager.initialize()
# ... operations ...
manager.shutdown()
```

### 2. Retrieve & Set Metadata

```python
# Retrieve metadata (auto-extracts if registered)
meta = manager.get_metadata("GeneFusionAI")
print(meta.purpose)
print(meta.primary_technologies)

# Update metadata
meta.supported_operations.append("deploy")
manager.set_metadata("GeneFusionAI", meta)
```

### 3. Check Supported Operations

```python
if manager.supports_operation("GeneFusionAI", "train"):
    print("GeneFusionAI supports 'train' operation!")

ops = manager.list_supported_operations("GeneFusionAI")
print("Supported ops:", ops)
```

### 4. Auto-Extraction

```python
extracted_meta = manager.extract_metadata_from_project("/path/to/project")
```

---

## Manifest Schema (`genova_project.json`)

Projects can define their metadata explicitly using `genova_project.json` at their project root:

```json
{
  "purpose": "Gene Fusion AI detection pipeline",
  "technologies": ["Python", "PyTorch"],
  "operations": ["inspect", "train", "predict"],
  "entry_points": {
    "train": "main.py --mode train",
    "predict": "main.py --mode predict"
  },
  "maintainers": ["Genova Nexus Team"],
  "tags": ["genomics", "ai"],
  "custom_attributes": {
    "recommended_gpu_vram_gb": 16
  }
}
```
