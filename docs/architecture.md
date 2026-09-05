# Architecture Overview — Genova Operator

Genova Operator is organized into modular layers designed to operate independently while providing unified operational interfaces.

## Philosophy: "Genova Nexus thinks, Genova Operator acts."

Genova Nexus serves as the high-level intelligent decision maker, while **Genova Operator** provides the practical capabilities required to inspect projects, execute commands, run experiments, monitor processes, manage automated jobs, and report structured results.

---

## Core Architecture & Configuration (Days 1–3)

```text
                       ┌─────────────────────────┐
                       │     GENOVA NEXUS        │
                       └────────────┬────────────┘
                                    │ TaskRequest / TaskResult
                                    ▼
                       ┌─────────────────────────┐
                       │     GenovaOperator      │  (Central Orchestrator)
                       └──────┬───────────┬──────┘
                              │           │
                     ┌────────┴───┐   ┌───┴─────────────┐
                     │  EventBus  │   │  ConfigManager  │
                     └────────────┘   └────────┬────────┘
                                               │
                                       ┌───────┴───────┐
                                       ▼               ▼
                                 GeneFusionAI       Clarify
                                 ProjectConfig   ProjectConfig
```

### Core Subsystems

1. **Orchestration Core** (`src/genova_operator/core/`):
   - `GenovaOperator`: Central control entry point.
   - `TaskRequest` & `TaskResult`: Standardized communication payloads.
   - `EventBus`: Thread-safe pub/sub event dispatcher.

2. **Configuration Subsystem (`Operator Config`)** (`src/genova_operator/config/`):
   - `ConfigManager`: Sub-component implementing `BaseComponent`.
   - Data models: `OperatorConfig`, `WorkspaceConfig`, `ExecutionConfig`, `MonitoringConfig`, `AutomationConfig`, `ProjectConfig`.
   - Layered overrides (Defaults $\rightarrow$ File $\rightarrow$ Dict $\rightarrow$ Environment Variables).
   - Independent project settings for `GeneFusionAI`, `Clarify`, and future additions.

---

## 60-Day Architecture Roadmap

1. **Phase 1: Foundation and Core Architecture** (Days 1–7)
   - Day 1: Project Foundation (Repository, Packaging, `.gitignore`)
   - Day 2: Core Architecture (`Operator Core`, Orchestrator, EventBus, Data Contracts)
   - Day 3: Configuration Manager (`Operator Config`)
   - Day 4: Workspace Manager
   - Day 5: Project Registry
   - Day 6: Project Discovery
   - Day 7: Foundation Validation
2. **Phase 2: Project Operations** (Days 8–14)
3. **Phase 3: Execution Engine** (Days 15–21)
4. **Phase 4: Monitoring and Observability** (Days 22–28)
5. **Phase 5: Git and Development Awareness** (Days 29–33)
6. **Phase 6: Automation** (Days 34–40)
7. **Phase 7: Pipelines and Research Operations** (Days 41–47)
8. **Phase 8: ML and AutoML Operations** (Days 48–52)
9. **Phase 9: Genova Nexus Integration** (Days 53–56)
10. **Phase 10: Production Validation and Release** (Days 57–60)
