# Architecture Overview — Genova Operator

Genova Operator is organized into modular layers designed to operate independently while providing unified operational interfaces.

## Philosophy: "Genova Nexus thinks, Genova Operator acts."

Genova Nexus serves as the high-level intelligent decision maker, while **Genova Operator** provides the practical capabilities required to inspect projects, execute commands, run experiments, monitor processes, manage automated jobs, and report structured results.

---

## System Subsystems (Phase 1 Completed, Phase 2 In Progress)

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
                                   ┌─────────────────────────┼─────────────────────────┐
                                   ▼                         ▼                         ▼
                            ProjectInspector           ProjectHealth            ProjectState
                            (Day 8: Inspect)          (Day 9: Health)          (Day 10: State)
                                   │                         │                         │
                                   └─────────────────────────┼─────────────────────────┘
                                                             │
                                                     ┌───────┴───────┐
                                                     ▼               ▼
                                               GeneFusionAI       Clarify
```

### Subsystems Overview

1. **Phase 1 Foundation Components** (Days 1–7):
   - `GenovaOperator` (Core Orchestrator & EventBus)
   - `ConfigManager` (`Operator Config`)
   - `WorkspaceManager` (`Workspace Manager`)
   - `ProjectRegistry` (`Project Registry`)
   - `ProjectDiscovery` (`Project Discovery`)
   - `CoreDiagnostics` (`Core Diagnostics`)

2. **Phase 2 Project Operations Components** (Days 8–14):
   - `ProjectInspector` (Day 8): Detailed inspection system analyzing directory structures (`DirectoryTree`), dependencies (`DependencySummary`), Git repositories (`RepositoryInspection`), environments (`EnvironmentInspection`), and entry points (`EntryPointsSummary`).
   - `ProjectHealthManager` (Day 9): 5-pillar project health assessment system checking project existence, configuration validity, runtime environment availability, dependency accessibility, and structural component presence.
   - `ProjectStateManager` (Day 10): Standard project state model (`AVAILABLE`, `ACTIVE`, `INACTIVE`, `RUNNING`, `UNHEALTHY`, `UNAVAILABLE`) linking active tasks, health updates, and state change event broadcasting (`StateTransitionRecord`).

---

## 60-Day Architecture Roadmap

1. **Phase 1: Foundation and Core Architecture** (Days 1–7) — **COMPLETED**
2. **Phase 2: Project Operations** (Days 8–14) — **IN PROGRESS**
   - Day 8: Project Inspector (`Project Inspector`) ✅
   - Day 9: Project Health (`Project Health`) ✅
   - Day 10: Project State (`Project State`) ✅
   - Day 11: Project Activity (`Project Activity`)
   - Day 12: Project Metadata (`Project Metadata`)
   - Day 13: Project Operations Manager (`Project Operations`)
   - Day 14: Genova Project Validation (`GeneFusionAI Adapter` + `Clarify Adapter`)
3. **Phase 3: Execution Engine** (Days 15–21)
4. **Phase 4: Monitoring and Observability** (Days 22–28)
5. **Phase 5: Git and Development Awareness** (Days 29–33)
6. **Phase 6: Automation** (Days 34–40)
7. **Phase 7: Pipelines and Research Operations** (Days 41–47)
8. **Phase 8: ML and AutoML Operations** (Days 48–52)
9. **Phase 9: Genova Nexus Integration** (Days 53–56)
10. **Phase 10: Production Validation and Release** (Days 57–60)
