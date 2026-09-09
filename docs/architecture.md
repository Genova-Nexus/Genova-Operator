# Architecture Overview — Genova Operator

Genova Operator is organized into modular layers designed to operate independently while providing unified operational interfaces.

## Philosophy: "Genova Nexus thinks, Genova Operator acts."

Genova Nexus serves as the high-level intelligent decision maker, while **Genova Operator** provides the practical capabilities required to inspect projects, execute commands, run experiments, monitor processes, manage automated jobs, and report structured results.

---

## Core Architecture, Config, Workspace, Registry, Discovery & Diagnostics (Phase 1 Completed)

```text
                       ┌─────────────────────────┐
                       │     GENOVA NEXUS        │
                       └────────────┬────────────┘
                                    │ TaskRequest / TaskResult
                                    ▼
                       ┌─────────────────────────┐
                       │     GenovaOperator      │  (Central Orchestrator)
                       └─┬──────────┬──────────┬─┘
                         │          │          │
           ┌─────────────┴┐   ┌─────┴───────┐  └─────────────┐
           │   EventBus   │   │ConfigManager│                │
           └──────────────┘   └─────┬───────┘                ▼
                                    │               ┌──────────────────┐
                                    ▼               │ WorkspaceManager │
                              ProjectConfigs        └────────┬─────────┘
                                                             │
                                                             ▼
                                                    ┌──────────────────┐
                                                    │ ProjectDiscovery │ (Auto-Discovery)
                                                    └────────┬─────────┘
                                                             │ Auto-Registers
                                                             ▼
                                                    ┌──────────────────┐
                                                    │ ProjectRegistry  │ (Source of Truth)
                                                    └────────┬─────────┘
                                                             │
                                                     ┌───────┴───────┐
                                                     ▼               ▼
                                               GeneFusionAI       Clarify
                                               ProjectRecord   ProjectRecord

                                 [ Core Diagnostics Component Active ]
```

### Core Subsystems (Phase 1)

1. **Orchestration Core** (`src/genova_operator/core/`):
   - `GenovaOperator`: Central control entry point.
   - `TaskRequest` & `TaskResult`: Standardized communication payloads.
   - `EventBus`: Thread-safe pub/sub event dispatcher.

2. **Configuration Subsystem (`Operator Config`)** (`src/genova_operator/config/`):
   - `ConfigManager`: Sub-component implementing `BaseComponent`.
   - Data models: `OperatorConfig`, `WorkspaceConfig`, `ExecutionConfig`, `MonitoringConfig`, `AutomationConfig`, `ProjectConfig`.

3. **Workspace Management Subsystem (`Workspace Manager`)** (`src/genova_operator/workspace/`):
   - `WorkspaceManager`: Sub-component enforcing path boundaries, workspace health diagnostics, candidate project directory resolution, and marker management.

4. **Project Registry Subsystem (`Project Registry`)** (`src/genova_operator/registry/`):
   - `ProjectRegistry`: Central source of truth component for project identity (`ProjectIdentity`), Git repository specs (`RepositoryInfo`), runtime environment specs (`EnvironmentInfo`), and comprehensive project records (`ProjectRecord`).

5. **Project Discovery Subsystem (`Project Discovery`)** (`src/genova_operator/discovery/`):
   - `ProjectDiscovery`: Automatic project detection component supporting rule-based evaluation (`rules.py`), confidence classification (`ProjectConfidence`), and auto-registration into `ProjectRegistry`.

6. **Core Diagnostics Subsystem (`Core Diagnostics`)** (`src/genova_operator/diagnostics/`):
   - `CoreDiagnostics`: System health validation component that runs system checks across all foundation components and generates structured `DiagnosticReport` reports.

---

## 60-Day Architecture Roadmap

1. **Phase 1: Foundation and Core Architecture** (Days 1–7) — **COMPLETED**
   - Day 1: Project Foundation (Repository, Packaging, `.gitignore`) ✅
   - Day 2: Core Architecture (`Operator Core`, Orchestrator, EventBus, Data Contracts) ✅
   - Day 3: Configuration Manager (`Operator Config`) ✅
   - Day 4: Workspace Manager (`Workspace Manager`) ✅
   - Day 5: Project Registry (`Project Registry`) ✅
   - Day 6: Project Discovery (`Project Discovery`) ✅
   - Day 7: Foundation Validation (`Core Diagnostics` & Phase 1 Milestone) ✅
2. **Phase 2: Project Operations** (Days 8–14)
3. **Phase 3: Execution Engine** (Days 15–21)
4. **Phase 4: Monitoring and Observability** (Days 22–28)
5. **Phase 5: Git and Development Awareness** (Days 29–33)
6. **Phase 6: Automation** (Days 34–40)
7. **Phase 7: Pipelines and Research Operations** (Days 41–47)
8. **Phase 8: ML and AutoML Operations** (Days 48–52)
9. **Phase 9: Genova Nexus Integration** (Days 53–56)
10. **Phase 10: Production Validation and Release** (Days 57–60)
